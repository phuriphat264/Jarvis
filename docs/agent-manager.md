# JARVIS Agent Manager Architecture (Phase 13)

## Overview
The Agent Manager elevates JARVIS from a single AI runtime into a multi-agent orchestration layer, seamlessly integrating various specialist capabilities without fragmenting the user experience. 

## Key Components

### 1. AgentRegistry
Registers `BaseSpecialistAgent` instances. Ensures unique naming and acts as the central hub for discovering available agent capabilities. 
Agents: `general`, `personal_os`, `research`, `document`, `vision`, `planning`, `communication`, `coding` (disabled by default).

### 2. AgentRouter
Interprets incoming user requests and rapidly classifies them. If a task requires only simple chat, it routes directly to `JarvisCore` to conserve tokens and time. If it demands specific logic (e.g. "Send a message via LINE"), it routes to the `CommunicationAgent`. Complex tasks involving multi-step processes are routed as `MULTI_AGENT`.

### 3. AgentManager
The core orchestrator. When assigned a `MULTI_AGENT` task:
1. It requests the LLM to construct a strictly structured JSON plan containing parallelizable execution steps.
2. It evaluates the dependencies of these steps.
3. It limits parallel execution (e.g., maximum of 2 concurrent agents) to prevent runaway costs or rate limits.
4. It waits for and synthesizes the final output, injecting it into the original `JarvisCore` context window so the user receives one unified answer.

### 4. GenericAgentWrapper
A bridge that binds the modern `SpecialistAgent` metadata (allowed tools, roles) to the legacy (Phase 6) `AgentRuntime`. This ensures that all specialist execution remains constrained by the exact same boundaries, tool limits, and permissions (including Phase 12 Confirmations) established previously.

## Security & Limits
- **Strict Confirmations**: `CommunicationAgent` or `PlanningAgent` creating external side effects still route through `ToolExecutor`. If an external write is attempted, it creates a `PendingAction` and halts. The LLM cannot confirm actions itself.
- **Coding Safety**: `CodingAgent` has `enabled = False` out-of-the-box. We do not permit unrestricted shell commands or arbitrary filesystem changes.
- **Timeouts & Recursion Defenses**: `MAX_AGENT_RUNTIME_SECONDS`, `MAX_PARALLEL_AGENTS` are strongly enforced. Agents cannot recursively spawn arbitrary unknown agents.

## Usage
The system routes dynamically from typical user inputs:
`"Hello JARVIS"` -> `SIMPLE_CHAT`
`"What is on my calendar?"` -> `PERSONAL_OS` (PersonalOSAgent)
`"Read this PDF, then find related latest news on the web."` -> `MULTI_AGENT` (DocumentAgent + ResearchAgent -> Synthesis)

Administrators can view runs, plans, and final state results in the `/agents` Dashboard UI.
