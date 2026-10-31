"""app.orchestrator facade for backward compatibility"""

from app.agent.orchestrator import AgentOrchestrator, MockAgentOrchestrator

__all__ = ["AgentOrchestrator", "MockAgentOrchestrator"]
