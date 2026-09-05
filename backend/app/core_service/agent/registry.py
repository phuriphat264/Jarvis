from typing import Dict, List, Optional
from app.interfaces.specialist_agent import BaseSpecialistAgent

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, BaseSpecialistAgent] = {}

    def register(self, agent: BaseSpecialistAgent) -> None:
        if agent.name in self._agents:
            raise ValueError(f"Agent '{agent.name}' is already registered.")
        self._agents[agent.name] = agent

    def unregister(self, agent_name: str) -> None:
        if agent_name in self._agents:
            del self._agents[agent_name]

    def get_agent(self, agent_name: str) -> Optional[BaseSpecialistAgent]:
        return self._agents.get(agent_name)

    def list_agents(self) -> List[BaseSpecialistAgent]:
        return list(self._agents.values())

    def get_enabled_agents(self) -> List[BaseSpecialistAgent]:
        return [a for a in self._agents.values() if a.enabled]

    def get_agent_metadata(self) -> List[Dict[str, str]]:
        return [a.get_metadata() for a in self.get_enabled_agents()]

agent_registry = AgentRegistry()
