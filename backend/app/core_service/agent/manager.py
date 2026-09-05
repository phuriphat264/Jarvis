import json
import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.sql import func
from app.database.session import AsyncSessionLocal
from app.database.models.agent_manager import AgentManagerRun
from app.core_service.agent.router import AgentRouter
from app.core_service.agent.registry import agent_registry
from app.interfaces.ai_provider import AIProviderFactory
from app.core.config import settings

logger = logging.getLogger("jarvis.agent_manager")

class AgentManager:
    def __init__(self):
        self.ai = AIProviderFactory.get_provider()

    async def _generate_plan(self, request: str, available_agents: List[Dict]) -> Dict[str, Any]:
        agents_info = json.dumps(available_agents, ensure_ascii=False, indent=2)
        system_prompt = (
            "You are the Agent Manager. Create a JSON structured plan to solve the user's task. "
            "Do NOT output executable code. Do NOT output anything outside the JSON.\n"
            f"Available Agents:\n{agents_info}\n\n"
            "Format:\n"
            "{\n"
            '  "task_summary": "...",\n'
            '  "steps": [\n'
            '    {"step_id": "step_1", "agent": "agent_name", "objective": "...", "depends_on": []}\n'
            "  ]\n"
            "}"
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request}
        ]
        
        try:
            response = await self.ai.generate_with_tools(messages, [])
            # Strip markdown code blocks if any
            content = response.content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to generate plan: {e}")
            return {"task_summary": "Fallback single step", "steps": [{"step_id": "step_1", "agent": "general", "objective": request, "depends_on": []}]}

    async def _execute_step(self, step: Dict[str, Any], context: Dict[str, Any], agent_runtime) -> Dict[str, Any]:
        agent_name = step.get("agent", "general")
        agent = agent_registry.get_agent(agent_name)
        if not agent or not getattr(agent, "enabled", True):
            agent = agent_registry.get_agent("general") # Fallback
            
        step_context = context.copy()
        step_context["objective"] = step.get("objective", "")
        
        try:
            # We enforce timeout here in case the agent wrapper doesn't
            result = await asyncio.wait_for(
                agent.execute(step_context, agent_runtime),
                timeout=settings.MAX_AGENT_RUNTIME_SECONDS
            )
            return {"step_id": step["step_id"], "success": result.success, "summary": result.summary, "error": result.error}
        except asyncio.TimeoutError:
            return {"step_id": step["step_id"], "success": False, "summary": "Timeout", "error": "Agent execution timed out."}
        except Exception as e:
            return {"step_id": step["step_id"], "success": False, "summary": "Error", "error": str(e)}

    async def run(self, user_id: int, request: str, agent_runtime, conversation_id: int = None, request_id: str = None) -> Dict[str, Any]:
        route = AgentRouter.classify_request(request)
        
        # Save run state
        async with AsyncSessionLocal() as db:
            run = AgentManagerRun(
                user_id=user_id,
                conversation_id=conversation_id,
                request_id=request_id,
                input_text=request,
                route_type=route,
                status="PLANNING"
            )
            db.add(run)
            await db.commit()
            await db.refresh(run)
            run_id = run.id
        
        context = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "request_id": request_id,
            "agent_manager_run_id": run_id
        }
        
        plan = None
        if route == "SIMPLE_CHAT":
            # Just return and let JarvisCore handle it directly for speed
            async with AsyncSessionLocal() as db:
                r = await db.get(AgentManagerRun, run_id)
                r.status = "COMPLETED"
                r.completed_at = func.now()
                await db.commit()
            return {"route": route, "results": []}
            
        elif route == "MULTI_AGENT":
            enabled_agents = agent_registry.get_agent_metadata()
            plan = await self._generate_plan(request, enabled_agents)
        else:
            # Single specialist
            agent_name = route.lower()
            plan = {
                "task_summary": request,
                "steps": [
                    {"step_id": "step_1", "agent": agent_name, "objective": request, "depends_on": []}
                ]
            }

        async with AsyncSessionLocal() as db:
            r = await db.get(AgentManagerRun, run_id)
            r.status = "RUNNING"
            r.plan = plan
            r.started_at = func.now()
            await db.commit()
            
        # Execute plan
        results = []
        pending_steps = plan.get("steps", [])
        completed_steps = {}
        
        # A simple dependency resolver and parallel execution limit
        while pending_steps:
            # Find ready steps (all dependencies completed successfully)
            ready_steps = []
            for step in pending_steps:
                deps = step.get("depends_on", [])
                if all(d in completed_steps and completed_steps[d] for d in deps):
                    ready_steps.append(step)
                    
            if not ready_steps:
                # Circular dependency or failed dependency
                break
                
            # Limit parallel agents
            ready_steps = ready_steps[:2] 
            
            # Execute concurrently
            tasks = [self._execute_step(s, context, agent_runtime) for s in ready_steps]
            step_results = await asyncio.gather(*tasks)
            
            for res, step in zip(step_results, ready_steps):
                results.append(res)
                completed_steps[res["step_id"]] = res["success"]
                pending_steps.remove(step)
                
        # Final synthesis
        async with AsyncSessionLocal() as db:
            r = await db.get(AgentManagerRun, run_id)
            r.status = "COMPLETED"
            r.final_result = json.dumps(results, ensure_ascii=False)
            r.completed_at = func.now()
            await db.commit()
            
        return {"route": route, "plan": plan, "results": results}

agent_manager = AgentManager()
