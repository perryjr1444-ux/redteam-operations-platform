"""
Attack Planner Integration - Bridges AI agents with red team operations

Integrates the 5 LangGraph agents into the attack execution pipeline:
1. Attack Planner: Generates attack strategies
2. Vulnerability Analyzer: Prioritizes findings
3. Exploit Advisor: Recommends techniques
4. Chain Optimizer: Improves efficiency
5. Agent Coordinator: Orchestrates all agents

This is the main interface for AI-powered autonomous red team operations.
"""

import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

from ..agents import (
    AgentCoordinator,
    AttackPlannerAgent,
    VulnerabilityAnalyzerAgent,
    ExploitAdvisorAgent,
    ChainOptimizerAgent,
)
from ..agents.agent_coordinator import AgentType

logger = logging.getLogger(__name__)


@dataclass
class AIAssistedAttackPlan:
    """AI-generated attack plan with full context"""
    target: str
    attack_plan: Any  # AttackPlan from agent
    vulnerability_analysis: Optional[Any] = None
    exploit_recommendations: List[Any] = None
    chain_optimizations: Optional[Any] = None
    confidence_score: float = 0.0
    generated_at: datetime = None


class AttackPlannerIntegration:
    """
    Main integration point for AI-powered attack planning.

    Coordinates all AI agents to provide autonomous attack planning,
    vulnerability analysis, and exploitation guidance.
    """

    def __init__(self, langgraph_url: Optional[str] = None, enable_agents: bool = True):
        self.langgraph_url = langgraph_url
        self.enable_agents = enable_agents

        # Initialize agent coordinator
        self.coordinator = AgentCoordinator(langgraph_url) if enable_agents else None

        logger.info(f"AI Attack Planner Integration initialized (agents: {'enabled' if enable_agents else 'disabled'})")

    async def plan_attack_autonomous(
        self,
        target: str,
        objectives: List[str],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> AIAssistedAttackPlan:
        """
        Generate a complete AI-assisted attack plan.

        This method coordinates all agents in parallel using fractal execution:
        1. Attack Planner generates strategy
        2. Vulnerability Analyzer prepares for findings
        3. Exploit Advisor prepares recommendations
        4. Chain Optimizer prepares for optimization

        Args:
            target: Target URL, IP, or domain
            objectives: Attack objectives
            constraints: Optional constraints (time, stealth, etc.)

        Returns:
            Complete AI-assisted attack plan
        """
        if not self.enable_agents:
            logger.warning("Agents disabled, returning basic plan")
            return self._generate_basic_plan(target, objectives)

        logger.info(f"Generating AI-assisted attack plan for {target}")

        # Delegate to agents in parallel using fractal execution
        attack_plan_task = self.coordinator.delegate_task(
            AgentType.ATTACK_PLANNER,
            "plan_attack",
            {"target": target, "objectives": objectives, "constraints": constraints or {}},
        )

        # Wait for attack plan
        attack_plan = await self.coordinator.get_task_result(attack_plan_task, wait=True)

        # Calculate overall confidence
        confidence = attack_plan.success_probability if hasattr(attack_plan, 'success_probability') else 0.7

        ai_plan = AIAssistedAttackPlan(
            target=target,
            attack_plan=attack_plan,
            confidence_score=confidence,
            generated_at=datetime.utcnow(),
        )

        logger.info(f"AI-assisted attack plan generated with {confidence:.0%} confidence")
        return ai_plan

    async def analyze_scan_results(
        self,
        scan_results: List[Dict[str, Any]],
        target: str,
    ) -> Any:
        """
        Analyze scan results using AI vulnerability analyzer.

        Delegates to Vulnerability Analyzer agent for intelligent analysis,
        prioritization, and actionable recommendations.
        """
        if not self.enable_agents:
            logger.warning("Agents disabled, returning raw results")
            return {"findings": scan_results, "analysis": "Agents disabled"}

        logger.info(f"Analyzing scan results for {target} using AI")

        task_id = await self.coordinator.delegate_task(
            AgentType.VULN_ANALYZER,
            "analyze_vulnerabilities",
            {"scan_results": scan_results, "target": target},
        )

        analysis = await self.coordinator.get_task_result(task_id, wait=True)
        logger.info(f"Vulnerability analysis complete: {analysis.total_findings if hasattr(analysis, 'total_findings') else 0} findings")

        return analysis

    async def get_exploit_recommendations(
        self,
        vulnerabilities: List[Dict[str, Any]],
    ) -> List[Any]:
        """
        Get exploitation recommendations for discovered vulnerabilities.

        Delegates to Exploit Advisor agent for technique recommendations.
        """
        if not self.enable_agents:
            return []

        logger.info(f"Getting exploit recommendations for {len(vulnerabilities)} vulnerabilities")

        # Delegate recommendations in parallel for each vulnerability
        tasks = []
        for vuln in vulnerabilities:
            task_id = await self.coordinator.delegate_task(
                AgentType.EXPLOIT_ADVISOR,
                "recommend_exploit",
                {"vulnerability": vuln},
            )
            tasks.append(task_id)

        # Wait for all recommendations
        recommendations = []
        for task_id in tasks:
            try:
                rec = await self.coordinator.get_task_result(task_id, wait=True, timeout=30.0)
                recommendations.append(rec)
            except Exception as e:
                logger.error(f"Failed to get recommendation for task {task_id}: {e}")

        logger.info(f"Generated {len(recommendations)} exploit recommendations")
        return recommendations

    async def optimize_chain(
        self,
        chain: Dict[str, Any],
        execution_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Any:
        """
        Optimize an attack chain using AI.

        Delegates to Chain Optimizer agent for performance analysis
        and optimization recommendations.
        """
        if not self.enable_agents:
            return None

        logger.info(f"Optimizing chain: {chain.get('id', 'unknown')}")

        task_id = await self.coordinator.delegate_task(
            AgentType.CHAIN_OPTIMIZER,
            "optimize_chain",
            {"chain": chain, "execution_history": execution_history or []},
        )

        optimization = await self.coordinator.get_task_result(task_id, wait=True)
        logger.info(f"Chain optimization complete: {optimization.estimated_improvement if hasattr(optimization, 'estimated_improvement') else 0:.1f}% improvement potential")

        return optimization

    async def get_consensus_recommendation(
        self,
        question: str,
        context: Dict[str, Any],
        agents: Optional[List[AgentType]] = None,
    ) -> Dict[str, Any]:
        """
        Get consensus recommendation from multiple agents.

        Uses fractal parallel execution to query all agents simultaneously
        and aggregate their responses.
        """
        if not self.enable_agents:
            return {"consensus": "Agents disabled", "confidence": 0.0}

        logger.info(f"Getting consensus recommendation on: {question}")

        consensus = await self.coordinator.consensus_decision(
            question, context, agents
        )

        logger.info(f"Consensus reached with {consensus.get('consensus_confidence', 0):.0%} confidence")
        return consensus

    def _generate_basic_plan(self, target: str, objectives: List[str]) -> AIAssistedAttackPlan:
        """Generate basic plan when agents are disabled"""
        return AIAssistedAttackPlan(
            target=target,
            attack_plan={
                "target": target,
                "strategy": "standard_pentest",
                "tools": ["nmap", "nikto", "sqlmap"],
                "notes": "Basic plan (AI agents disabled)",
            },
            confidence_score=0.5,
            generated_at=datetime.utcnow(),
        )

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all AI agents"""
        if not self.enable_agents or not self.coordinator:
            return {"enabled": False}

        return {
            "enabled": True,
            "coordinator_stats": self.coordinator.get_coordinator_stats(),
            "agent_status": self.coordinator.get_agent_status(),
        }
