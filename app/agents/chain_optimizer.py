"""
Chain Optimizer Agent - Attack Chain Efficiency Optimization

Uses AI to:
- Analyze attack chain performance and success rates
- Identify bottlenecks and inefficiencies
- Recommend chain improvements and optimizations
- Suggest parallel execution opportunities
- Learn from execution history to improve future chains
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChainOptimization:
    """Optimization recommendation for an attack chain"""
    chain_id: str
    current_performance: Dict[str, Any]
    bottlenecks: List[str]
    optimizations: List[Dict[str, Any]]
    estimated_improvement: float  # Percentage improvement
    parallel_opportunities: List[str]
    recommended_changes: List[str]
    generated_at: datetime


class ChainOptimizerAgent:
    """AI agent for attack chain optimization and performance improvement"""

    def __init__(self, langgraph_url: Optional[str] = None):
        self.langgraph_url = langgraph_url
        self.optimization_history: List[ChainOptimization] = []
        logger.info("Chain Optimizer Agent initialized")

    async def execute(self, operation: str, input_data: Dict[str, Any]) -> Any:
        """Execute an operation"""
        if operation == "optimize_chain":
            return await self.optimize_chain(
                input_data.get("chain"),
                input_data.get("execution_history", []),
            )
        elif operation == "analyze":
            return await self.analyze_question(
                input_data.get("question"),
                input_data.get("context", {}),
            )
        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def optimize_chain(
        self,
        chain: Dict[str, Any],
        execution_history: List[Dict[str, Any]],
    ) -> ChainOptimization:
        """Analyze and optimize an attack chain"""
        chain_id = chain.get("id", "unknown")
        logger.info(f"Optimizing chain: {chain_id}")

        # Analyze current performance
        current_perf = self._analyze_performance(chain, execution_history)

        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(chain, execution_history)

        # Generate optimization recommendations
        optimizations = self._generate_optimizations(chain, bottlenecks, current_perf)

        # Find parallel execution opportunities
        parallel_opps = self._find_parallel_opportunities(chain)

        # Calculate estimated improvement
        estimated_improvement = self._estimate_improvement(optimizations, parallel_opps)

        # Generate recommended changes
        recommendations = self._generate_recommendations(optimizations, parallel_opps)

        optimization = ChainOptimization(
            chain_id=chain_id,
            current_performance=current_perf,
            bottlenecks=bottlenecks,
            optimizations=optimizations,
            estimated_improvement=estimated_improvement,
            parallel_opportunities=parallel_opps,
            recommended_changes=recommendations,
            generated_at=datetime.utcnow(),
        )

        self.optimization_history.append(optimization)
        logger.info(f"Chain optimization complete: {estimated_improvement:.1f}% improvement potential")

        return optimization

    def _analyze_performance(
        self,
        chain: Dict[str, Any],
        execution_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Analyze current chain performance"""
        if not execution_history:
            return {
                "avg_duration": 0,
                "success_rate": 0,
                "executions": 0,
                "avg_tools_per_execution": len(chain.get("steps", [])),
            }

        durations = [h.get("duration", 0) for h in execution_history]
        successes = sum(1 for h in execution_history if h.get("status") == "completed")

        return {
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "success_rate": successes / len(execution_history) if execution_history else 0,
            "executions": len(execution_history),
            "avg_tools_per_execution": len(chain.get("steps", [])),
        }

    def _identify_bottlenecks(
        self,
        chain: Dict[str, Any],
        execution_history: List[Dict[str, Any]],
    ) -> List[str]:
        """Identify performance bottlenecks"""
        bottlenecks = []

        # Check for sequential execution that could be parallel
        steps = chain.get("steps", [])
        sequential_count = sum(1 for s in steps if not s.get("parallel", False))
        if sequential_count > 3:
            bottlenecks.append(f"{sequential_count} steps executing sequentially - parallelization opportunity")

        # Check for slow steps
        if execution_history:
            for step in steps:
                step_tool = step.get("tool")
                if step_tool in ["nmap", "masscan"]:  # Known slow tools
                    bottlenecks.append(f"Tool '{step_tool}' may cause delays - consider optimization")

        # Check for redundant steps
        step_tools = [s.get("tool") for s in steps]
        if len(step_tools) != len(set(step_tools)):
            bottlenecks.append("Duplicate tools detected - may indicate redundancy")

        return bottlenecks

    def _generate_optimizations(
        self,
        chain: Dict[str, Any],
        bottlenecks: List[str],
        current_perf: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate specific optimization recommendations"""
        optimizations = []

        # Parallel execution optimization
        if "sequentially" in " ".join(bottlenecks):
            optimizations.append({
                "type": "parallelization",
                "description": "Convert independent sequential steps to parallel execution",
                "impact": "high",
                "difficulty": "low",
                "estimated_speedup": 2.5,
            })

        # Tool-specific optimizations
        if "nmap" in " ".join(bottlenecks):
            optimizations.append({
                "type": "tool_optimization",
                "description": "Use nmap with optimized timing template (-T4) and targeted port ranges",
                "impact": "medium",
                "difficulty": "low",
                "estimated_speedup": 1.5,
            })

        # Redundancy elimination
        if "redundancy" in " ".join(bottlenecks):
            optimizations.append({
                "type": "redundancy_removal",
                "description": "Remove or consolidate duplicate tool executions",
                "impact": "medium",
                "difficulty": "low",
                "estimated_speedup": 1.3,
            })

        # Caching optimization
        optimizations.append({
            "type": "caching",
            "description": "Cache reconnaissance results to avoid re-scanning in subsequent executions",
            "impact": "high",
            "difficulty": "medium",
            "estimated_speedup": 2.0,
        })

        return optimizations

    def _find_parallel_opportunities(self, chain: Dict[str, Any]) -> List[str]:
        """Find steps that can be executed in parallel"""
        opportunities = []
        steps = chain.get("steps", [])

        # Group steps by dependencies
        independent_groups = []
        for i, step in enumerate(steps):
            depends_on = step.get("depends_on", [])
            if not depends_on:
                independent_groups.append(f"Step {i}: {step.get('tool')}")

        if len(independent_groups) > 1:
            opportunities.append(f"Can run {len(independent_groups)} independent reconnaissance steps in parallel")

        # Specific tool combinations that work well in parallel
        tools = [s.get("tool") for s in steps]
        if "nmap" in tools and "nikto" in tools:
            opportunities.append("Nmap and Nikto can execute simultaneously for faster scanning")

        if "sqlmap" in tools and "gobuster" in tools:
            opportunities.append("SQLMap and Gobuster can run in parallel for comprehensive assessment")

        return opportunities

    def _estimate_improvement(
        self,
        optimizations: List[Dict[str, Any]],
        parallel_opportunities: List[str],
    ) -> float:
        """Estimate overall performance improvement percentage"""
        if not optimizations:
            return 0.0

        # Compound speedups
        total_speedup = 1.0
        for opt in optimizations:
            speedup = opt.get("estimated_speedup", 1.0)
            if opt.get("impact") == "high":
                total_speedup *= speedup

        # Parallel opportunities add bonus
        if parallel_opportunities:
            total_speedup *= 1.2

        improvement_pct = (total_speedup - 1.0) * 100
        return min(improvement_pct, 80.0)  # Cap at 80% improvement

    def _generate_recommendations(
        self,
        optimizations: List[Dict[str, Any]],
        parallel_opportunities: List[str],
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # High-impact optimizations first
        high_impact = [o for o in optimizations if o.get("impact") == "high"]
        for opt in high_impact:
            recommendations.append(f"[HIGH PRIORITY] {opt['description']}")

        # Parallel opportunities
        for opp in parallel_opportunities:
            recommendations.append(f"[PARALLELIZATION] {opp}")

        # Medium-impact optimizations
        medium_impact = [o for o in optimizations if o.get("impact") == "medium"]
        for opt in medium_impact:
            recommendations.append(f"[OPTIMIZATION] {opt['description']}")

        return recommendations

    async def analyze_question(self, question: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze question from chain optimization perspective"""
        return {
            "agent": "chain_optimizer",
            "analysis": f"Chain optimization perspective on: {question}",
            "recommendation": "Recommend analyzing execution history to identify optimization opportunities",
            "confidence": 0.75,
        }
