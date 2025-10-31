"""
Agent Manager - Central Management for AI Agent System

Provides a unified interface for managing all AI agents, coordinating
fractal parallel execution, and integrating with the redteam platform.

Features:
- Agent lifecycle management
- Health monitoring
- Performance tracking
- Load balancing
- Error handling and recovery
"""

import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from ..agents import AgentCoordinator, AgentType
from .attack_integration import AttackPlannerIntegration
from ..fractal_orchestrator import (
    FractalOrchestrator,
    ExecutionNode,
    ExecutionLevel,
    ResourcePool,
    create_agent_node,
)

logger = logging.getLogger(__name__)


@dataclass
class AgentHealthStatus:
    """Health status for an agent"""
    agent_type: str
    is_healthy: bool
    last_check: datetime
    error_count: int
    avg_response_time: float
    uptime_percentage: float


class AgentManager:
    """
    Central manager for all AI agents in the red team platform.

    Integrates:
    - 5 specialized LangGraph agents
    - Fractal orchestrator for parallel execution
    - Attack planner integration
    - Health monitoring and recovery
    """

    def __init__(
        self,
        langgraph_url: Optional[str] = None,
        enable_agents: bool = True,
        enable_fractal: bool = True,
    ):
        self.langgraph_url = langgraph_url
        self.enable_agents = enable_agents
        self.enable_fractal = enable_fractal

        # Initialize components
        self.coordinator = AgentCoordinator(langgraph_url) if enable_agents else None
        self.attack_planner = AttackPlannerIntegration(langgraph_url, enable_agents)
        self.orchestrator = FractalOrchestrator() if enable_fractal else None

        # Health monitoring
        self.health_status: Dict[str, AgentHealthStatus] = {}
        self.health_check_interval = 60  # seconds
        self.monitoring_task: Optional[asyncio.Task] = None

        # Statistics
        self.total_operations = 0
        self.successful_operations = 0
        self.failed_operations = 0
        self.start_time = datetime.utcnow()

        logger.info(f"Agent Manager initialized (agents: {enable_agents}, fractal: {enable_fractal})")

    async def initialize(self):
        """Initialize the agent management system"""
        logger.info("Initializing Agent Manager...")

        # Initialize health status for all agents
        if self.enable_agents:
            for agent_type in AgentType:
                self.health_status[agent_type.value] = AgentHealthStatus(
                    agent_type=agent_type.value,
                    is_healthy=True,
                    last_check=datetime.utcnow(),
                    error_count=0,
                    avg_response_time=0.0,
                    uptime_percentage=100.0,
                )

        # Start health monitoring
        if self.enable_agents:
            self.monitoring_task = asyncio.create_task(self._health_monitoring_loop())

        logger.info("Agent Manager initialized successfully")

    async def shutdown(self):
        """Gracefully shutdown the agent manager"""
        logger.info("Shutting down Agent Manager...")

        # Stop health monitoring
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Agent Manager shutdown complete")

    async def plan_attack(
        self,
        target: str,
        objectives: List[str],
        constraints: Optional[Dict[str, Any]] = None,
        use_fractal: bool = True,
    ) -> Any:
        """
        Plan an attack using AI agents with optional fractal orchestration.

        Args:
            target: Target URL/IP/domain
            objectives: Attack objectives
            constraints: Optional constraints
            use_fractal: Use fractal orchestrator for parallel planning

        Returns:
            AI-assisted attack plan
        """
        self.total_operations += 1

        try:
            if use_fractal and self.enable_fractal:
                # Use fractal orchestrator for parallel planning
                return await self._plan_attack_fractal(target, objectives, constraints)
            else:
                # Direct planning without fractal orchestration
                plan = await self.attack_planner.plan_attack_autonomous(
                    target, objectives, constraints
                )
                self.successful_operations += 1
                return plan

        except Exception as e:
            logger.error(f"Attack planning failed: {e}")
            self.failed_operations += 1
            raise

    async def _plan_attack_fractal(
        self,
        target: str,
        objectives: List[str],
        constraints: Optional[Dict[str, Any]],
    ) -> Any:
        """Plan attack using fractal orchestration"""
        logger.info(f"Planning attack with fractal orchestration: {target}")

        # Create execution nodes for parallel planning
        root_node = create_agent_node("planning_root", "attack_planner")
        self.orchestrator.register_node(root_node)

        # Create child nodes for parallel analysis
        nodes = [
            create_agent_node("plan_strategy", "attack_planner", parent_id=root_node.id),
            create_agent_node("analyze_target", "vuln_analyzer", parent_id=root_node.id),
            create_agent_node("recommend_tools", "exploit_advisor", parent_id=root_node.id),
        ]

        for node in nodes:
            self.orchestrator.register_node(node)

        # Define executors for each level
        async def execute_agent(node: ExecutionNode) -> Any:
            """Execute agent based on node type"""
            if node.type == "attack_planner":
                return await self.attack_planner.plan_attack_autonomous(
                    target, objectives, constraints
                )
            # Add other agent executions as needed
            return {"status": "executed", "node": node.id}

        level_executors = {
            ExecutionLevel.META: execute_agent,
        }

        # Execute fractal orchestration
        summary = await self.orchestrator.execute_fractal(
            root_node.id,
            level_executors,
            max_parallel=5,
        )

        self.successful_operations += 1
        logger.info(f"Fractal attack planning complete: {summary['completed']} nodes")

        # Return the planning result from root node
        return self.orchestrator.get_node(root_node.id).result

    async def analyze_vulnerabilities(
        self,
        scan_results: List[Dict[str, Any]],
        target: str,
        get_exploit_recommendations: bool = True,
    ) -> Dict[str, Any]:
        """
        Analyze scan results with vulnerability analyzer.

        Optionally gets exploit recommendations in parallel.
        """
        self.total_operations += 1

        try:
            # Analyze vulnerabilities
            analysis = await self.attack_planner.analyze_scan_results(
                scan_results, target
            )

            result = {"analysis": analysis}

            # Get exploit recommendations in parallel if requested
            if get_exploit_recommendations and hasattr(analysis, 'findings'):
                vulns = [
                    {
                        "id": f.id if hasattr(f, 'id') else str(i),
                        "title": f.title if hasattr(f, 'title') else "Unknown",
                        "severity": f.severity if hasattr(f, 'severity') else "medium",
                    }
                    for i, f in enumerate(analysis.findings[:10])  # Limit to top 10
                ]

                recommendations = await self.attack_planner.get_exploit_recommendations(vulns)
                result["exploit_recommendations"] = recommendations

            self.successful_operations += 1
            return result

        except Exception as e:
            logger.error(f"Vulnerability analysis failed: {e}")
            self.failed_operations += 1
            raise

    async def optimize_chain(
        self,
        chain: Dict[str, Any],
        execution_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Any:
        """Optimize an attack chain using Chain Optimizer agent"""
        self.total_operations += 1

        try:
            optimization = await self.attack_planner.optimize_chain(
                chain, execution_history
            )
            self.successful_operations += 1
            return optimization

        except Exception as e:
            logger.error(f"Chain optimization failed: {e}")
            self.failed_operations += 1
            raise

    async def execute_consensus_decision(
        self,
        question: str,
        context: Dict[str, Any],
        agents: Optional[List[AgentType]] = None,
    ) -> Dict[str, Any]:
        """Get consensus decision from multiple agents"""
        self.total_operations += 1

        try:
            consensus = await self.attack_planner.get_consensus_recommendation(
                question, context, agents
            )
            self.successful_operations += 1
            return consensus

        except Exception as e:
            logger.error(f"Consensus decision failed: {e}")
            self.failed_operations += 1
            raise

    async def _health_monitoring_loop(self):
        """Background task for continuous health monitoring"""
        logger.info("Health monitoring started")

        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_checks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")

    async def _perform_health_checks(self):
        """Perform health checks on all agents"""
        if not self.coordinator:
            return

        agent_status = self.coordinator.get_agent_status()

        for agent_type_str, status in agent_status.items():
            if agent_type_str in self.health_status:
                health = self.health_status[agent_type_str]
                health.last_check = datetime.utcnow()

                # Update health based on agent status
                if status.get("tasks_failed", 0) > status.get("tasks_completed", 1) * 0.5:
                    health.is_healthy = False
                    health.error_count += 1
                else:
                    health.is_healthy = True

                # Update avg response time
                health.avg_response_time = status.get("avg_execution_time", 0.0)

                # Calculate uptime percentage
                if health.error_count > 0:
                    total_checks = health.error_count + status.get("tasks_completed", 0)
                    health.uptime_percentage = (
                        (total_checks - health.error_count) / total_checks * 100
                        if total_checks > 0 else 100.0
                    )

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all agents"""
        return {
            "enabled": self.enable_agents,
            "fractal_enabled": self.enable_fractal,
            "agents": {
                agent_type: {
                    "is_healthy": status.is_healthy,
                    "last_check": status.last_check.isoformat(),
                    "error_count": status.error_count,
                    "avg_response_time": status.avg_response_time,
                    "uptime_percentage": status.uptime_percentage,
                }
                for agent_type, status in self.health_status.items()
            },
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        success_rate = (
            self.successful_operations / self.total_operations * 100
            if self.total_operations > 0 else 0.0
        )

        return {
            "uptime_seconds": uptime,
            "total_operations": self.total_operations,
            "successful_operations": self.successful_operations,
            "failed_operations": self.failed_operations,
            "success_rate": success_rate,
            "health_status": self.get_health_status(),
            "agent_stats": self.attack_planner.get_agent_status() if self.enable_agents else {},
        }

    def get_capabilities(self) -> List[str]:
        """Get list of available capabilities"""
        capabilities = [
            "autonomous_attack_planning",
            "vulnerability_analysis",
            "exploit_recommendations",
            "chain_optimization",
            "consensus_decision_making",
        ]

        if self.enable_fractal:
            capabilities.append("fractal_parallel_execution")

        return capabilities
