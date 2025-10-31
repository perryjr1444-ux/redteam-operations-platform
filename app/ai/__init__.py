"""
AI Integration Package

Integrates LangGraph agents into the red team platform for autonomous operations.
Provides:
- Attack planning and strategy generation
- Vulnerability analysis and prioritization
- Exploitation guidance
- Chain optimization
- Real-time decision making

Version: 1.0.0
"""

from .attack_integration import AttackPlannerIntegration
from .agent_manager import AgentManager

__all__ = ["AttackPlannerIntegration", "AgentManager"]
