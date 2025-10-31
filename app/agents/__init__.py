"""
LangGraph Agent Integration Package

Provides autonomous AI agents for red team operations:
- Attack Planner: Strategic attack planning and target analysis
- Vulnerability Analyzer: Intelligent vulnerability assessment
- Exploit Advisor: Exploitation technique recommendations
- Chain Optimizer: Attack chain efficiency optimization
- Agent Coordinator: Meta-agent managing other agents

Version: 1.0.0
"""

from .agent_coordinator import AgentCoordinator, AgentType
from .attack_planner import AttackPlannerAgent
from .vuln_analyzer import VulnerabilityAnalyzerAgent
from .exploit_advisor import ExploitAdvisorAgent
from .chain_optimizer import ChainOptimizerAgent

__all__ = [
    "AgentCoordinator",
    "AgentType",
    "AttackPlannerAgent",
    "VulnerabilityAnalyzerAgent",
    "ExploitAdvisorAgent",
    "ChainOptimizerAgent",
]
