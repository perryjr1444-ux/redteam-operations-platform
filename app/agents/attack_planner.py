"""
Attack Planner Agent - Autonomous Attack Planning and Strategy

Uses AI to:
- Analyze target information and fingerprint
- Generate attack strategies and paths
- Recommend tool sequences
- Estimate success probabilities
- Adapt plans based on reconnaissance results
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class AttackPlan:
    """Generated attack plan"""
    target: str
    strategy: str  # "reconnaissance", "exploitation", "post-exploitation"
    recommended_chains: List[Dict[str, Any]]
    tools: List[str]
    estimated_duration: float
    success_probability: float
    risk_level: str  # "low", "medium", "high"
    notes: str
    generated_at: datetime


class AttackPlannerAgent:
    """
    AI agent for autonomous attack planning.

    Analyzes targets and generates intelligent attack strategies
    with recommended tool chains and success estimates.
    """

    def __init__(self, langgraph_url: Optional[str] = None):
        self.langgraph_url = langgraph_url
        self.planning_history: List[AttackPlan] = []
        logger.info("Attack Planner Agent initialized")

    async def execute(self, operation: str, input_data: Dict[str, Any]) -> Any:
        """Execute an operation"""
        if operation == "plan_attack":
            return await self.plan_attack(
                input_data.get("target"),
                input_data.get("objectives", []),
                input_data.get("constraints", {}),
            )
        elif operation == "analyze":
            return await self.analyze_question(
                input_data.get("question"),
                input_data.get("context", {}),
            )
        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def plan_attack(
        self,
        target: str,
        objectives: List[str],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> AttackPlan:
        """
        Generate an intelligent attack plan for a target.

        Args:
            target: Target URL, IP, or domain
            objectives: List of objectives (e.g., ["find_vulns", "exploit", "maintain_access"])
            constraints: Optional constraints (time limit, stealth level, etc.)
        """
        logger.info(f"Planning attack for target: {target}")

        constraints = constraints or {}

        # Analyze target type
        target_type = self._detect_target_type(target)

        # Generate strategy based on objectives
        strategy = self._select_strategy(objectives, target_type)

        # Recommend tool chains
        recommended_chains = self._generate_tool_chains(target_type, objectives, strategy)

        # Extract all tools
        tools = []
        for chain in recommended_chains:
            tools.extend(chain.get("tools", []))

        # Estimate execution time
        estimated_duration = self._estimate_duration(recommended_chains)

        # Calculate success probability
        success_probability = self._calculate_success_probability(target_type, strategy, constraints)

        # Determine risk level
        risk_level = self._assess_risk(strategy, constraints)

        # Generate notes
        notes = self._generate_planning_notes(target, target_type, strategy, objectives)

        plan = AttackPlan(
            target=target,
            strategy=strategy,
            recommended_chains=recommended_chains,
            tools=list(set(tools)),  # Deduplicate
            estimated_duration=estimated_duration,
            success_probability=success_probability,
            risk_level=risk_level,
            notes=notes,
            generated_at=datetime.utcnow(),
        )

        self.planning_history.append(plan)
        logger.info(f"Generated attack plan: {strategy} with {len(recommended_chains)} chains")

        return plan

    def _detect_target_type(self, target: str) -> str:
        """Detect target type from URL/IP"""
        if target.startswith("http://") or target.startswith("https://"):
            return "web_application"
        elif ":" in target and target.count(":") >= 2:  # IPv6
            return "network_host"
        elif target.replace(".", "").replace(":", "").isdigit():
            return "network_host"
        elif "." in target:
            return "domain"
        else:
            return "unknown"

    def _select_strategy(self, objectives: List[str], target_type: str) -> str:
        """Select optimal strategy based on objectives"""
        if "exploit" in objectives or "maintain_access" in objectives:
            return "full_engagement"
        elif "find_vulns" in objectives:
            return "vulnerability_assessment"
        elif "recon" in objectives or "enumerate" in objectives:
            return "reconnaissance"
        else:
            return "standard_pentest"

    def _generate_tool_chains(
        self,
        target_type: str,
        objectives: List[str],
        strategy: str,
    ) -> List[Dict[str, Any]]:
        """Generate recommended attack chains"""
        chains = []

        if target_type == "web_application":
            # Web application attack chains
            chains.append({
                "name": "Web Reconnaissance",
                "tools": ["nmap", "nikto", "gobuster"],
                "parallel": True,
                "description": "Initial web application fingerprinting and directory enumeration",
            })

            if "find_vulns" in objectives or "exploit" in objectives:
                chains.append({
                    "name": "Web Vulnerability Scanning",
                    "tools": ["sqlmap", "nikto", "wpscan"],
                    "parallel": False,
                    "description": "Automated vulnerability detection (SQL injection, CMS vulns)",
                })

        elif target_type == "network_host" or target_type == "domain":
            # Network/domain attack chains
            chains.append({
                "name": "Network Discovery",
                "tools": ["nmap", "masscan"],
                "parallel": True,
                "description": "Port scanning and service enumeration",
            })

            chains.append({
                "name": "Service Enumeration",
                "tools": ["nmap", "enum4linux"],
                "parallel": False,
                "description": "Detailed service version detection and enumeration",
            })

        # Add exploitation chains if needed
        if "exploit" in objectives:
            chains.append({
                "name": "Exploitation",
                "tools": ["metasploit", "custom_exploits"],
                "parallel": False,
                "description": "Exploit identified vulnerabilities",
            })

        return chains

    def _estimate_duration(self, chains: List[Dict[str, Any]]) -> float:
        """Estimate total execution duration in seconds"""
        # Simple estimation based on number of chains and tools
        total_tools = sum(len(chain.get("tools", [])) for chain in chains)
        base_time = 60  # 1 minute per tool
        return total_tools * base_time

    def _calculate_success_probability(
        self,
        target_type: str,
        strategy: str,
        constraints: Dict[str, Any],
    ) -> float:
        """Calculate estimated success probability (0.0 to 1.0)"""
        # Baseline by target type
        base_probability = {
            "web_application": 0.7,
            "network_host": 0.6,
            "domain": 0.5,
            "unknown": 0.4,
        }.get(target_type, 0.5)

        # Adjust for strategy
        strategy_modifier = {
            "reconnaissance": 0.9,
            "vulnerability_assessment": 0.8,
            "standard_pentest": 0.6,
            "full_engagement": 0.5,
        }.get(strategy, 0.6)

        # Adjust for constraints
        if constraints.get("time_limit"):
            strategy_modifier *= 0.9
        if constraints.get("stealth_mode"):
            strategy_modifier *= 0.8

        return min(1.0, base_probability * strategy_modifier)

    def _assess_risk(self, strategy: str, constraints: Dict[str, Any]) -> str:
        """Assess risk level of the attack plan"""
        if strategy in ["reconnaissance", "vulnerability_assessment"]:
            return "low"
        elif strategy == "standard_pentest":
            return "medium"
        elif strategy == "full_engagement":
            return "high"
        return "medium"

    def _generate_planning_notes(
        self,
        target: str,
        target_type: str,
        strategy: str,
        objectives: List[str],
    ) -> str:
        """Generate human-readable planning notes"""
        notes = f"Attack plan generated for {target_type} target: {target}\n"
        notes += f"Strategy: {strategy.replace('_', ' ').title()}\n"
        notes += f"Objectives: {', '.join(objectives)}\n"
        notes += "\nRecommendations:\n"
        notes += "- Execute reconnaissance chains first to gather target information\n"
        notes += "- Monitor for defensive responses and adjust strategy accordingly\n"
        notes += "- Document all findings for reporting\n"
        return notes

    async def analyze_question(self, question: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a question and provide attack planning perspective"""
        return {
            "agent": "attack_planner",
            "analysis": f"Attack planning perspective on: {question}",
            "recommendation": "Recommend analyzing target characteristics before attack execution",
            "confidence": 0.8,
        }
