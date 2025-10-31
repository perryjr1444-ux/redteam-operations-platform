"""
Agent Coordinator - Meta-Agent for Managing Other Agents

Coordinates all AI agents in the red team platform, managing:
- Agent lifecycle and execution
- Inter-agent communication
- Task delegation and load balancing
- Consensus decision-making
- Conflict resolution

Uses fractal parallel execution to run multiple agents concurrently.
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Types of specialized agents"""
    ATTACK_PLANNER = "attack_planner"
    VULN_ANALYZER = "vuln_analyzer"
    EXPLOIT_ADVISOR = "exploit_advisor"
    CHAIN_OPTIMIZER = "chain_optimizer"


@dataclass
class AgentTask:
    """Task to be executed by an agent"""
    id: str
    agent_type: AgentType
    operation: str  # "plan_attack", "analyze_vulnerabilities", etc.
    input_data: Dict[str, Any]
    priority: int = 1
    timeout: float = 300.0  # 5 minutes default
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class AgentStatus:
    """Status of an agent"""
    agent_type: AgentType
    is_active: bool = False
    current_task: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    avg_execution_time: float = 0.0
    last_active: Optional[datetime] = None


class AgentCoordinator:
    """
    Meta-agent that coordinates all other AI agents.

    Implements fractal parallel execution by managing multiple agents
    working concurrently on different aspects of red team operations.
    """

    def __init__(self, langgraph_url: Optional[str] = None, max_parallel_agents: int = 5):
        self.langgraph_url = langgraph_url
        self.max_parallel_agents = max_parallel_agents

        # Agent registry
        self.agents: Dict[AgentType, AgentStatus] = {
            agent_type: AgentStatus(agent_type=agent_type)
            for agent_type in AgentType
        }

        # Task management
        self.task_queue: List[AgentTask] = []
        self.active_tasks: Dict[str, AgentTask] = {}
        self.completed_tasks: Dict[str, AgentTask] = {}

        # Statistics
        self.total_tasks_delegated = 0
        self.total_tasks_completed = 0

        logger.info(f"Agent Coordinator initialized (max_parallel: {max_parallel_agents})")

    async def delegate_task(
        self,
        agent_type: AgentType,
        operation: str,
        input_data: Dict[str, Any],
        priority: int = 1,
    ) -> str:
        """
        Delegate a task to a specific agent.

        Returns: Task ID for tracking
        """
        task = AgentTask(
            id=f"task_{self.total_tasks_delegated}_{agent_type.value}",
            agent_type=agent_type,
            operation=operation,
            input_data=input_data,
            priority=priority,
        )

        self.task_queue.append(task)
        self.total_tasks_delegated += 1

        logger.info(f"Delegated task {task.id} to {agent_type.value}: {operation}")
        return task.id

    async def delegate_parallel(
        self,
        tasks: List[tuple[AgentType, str, Dict[str, Any]]],  # (agent_type, operation, input_data)
        wait_for_all: bool = True,
    ) -> List[str]:
        """
        Delegate multiple tasks in parallel to different agents.

        Args:
            tasks: List of (agent_type, operation, input_data) tuples
            wait_for_all: If True, wait for all tasks to complete

        Returns:
            List of task IDs
        """
        task_ids = []
        for agent_type, operation, input_data in tasks:
            task_id = await self.delegate_task(agent_type, operation, input_data)
            task_ids.append(task_id)

        if wait_for_all:
            # Execute all tasks in parallel
            await self.execute_parallel_tasks(task_ids)

        return task_ids

    async def execute_parallel_tasks(self, task_ids: List[str]) -> Dict[str, Any]:
        """Execute multiple tasks in parallel using fractal orchestration"""
        tasks = [
            self._execute_task(task_id)
            for task_id in task_ids
            if any(t.id == task_id for t in self.task_queue)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            task_id: result if not isinstance(result, Exception) else str(result)
            for task_id, result in zip(task_ids, results)
        }

    async def _execute_task(self, task_id: str) -> Any:
        """Execute a single task"""
        # Find task in queue
        task = next((t for t in self.task_queue if t.id == task_id), None)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        # Remove from queue, add to active
        self.task_queue.remove(task)
        self.active_tasks[task_id] = task

        # Update agent status
        agent_status = self.agents[task.agent_type]
        agent_status.is_active = True
        agent_status.current_task = task_id
        agent_status.last_active = datetime.utcnow()

        try:
            logger.info(f"Executing task {task_id} with {task.agent_type.value}")

            # Get the appropriate agent
            if task.agent_type == AgentType.ATTACK_PLANNER:
                from .attack_planner import AttackPlannerAgent

                agent = AttackPlannerAgent(self.langgraph_url)
                result = await agent.execute(task.operation, task.input_data)

            elif task.agent_type == AgentType.VULN_ANALYZER:
                from .vuln_analyzer import VulnerabilityAnalyzerAgent

                agent = VulnerabilityAnalyzerAgent(self.langgraph_url)
                result = await agent.execute(task.operation, task.input_data)

            elif task.agent_type == AgentType.EXPLOIT_ADVISOR:
                from .exploit_advisor import ExploitAdvisorAgent

                agent = ExploitAdvisorAgent(self.langgraph_url)
                result = await agent.execute(task.operation, task.input_data)

            elif task.agent_type == AgentType.CHAIN_OPTIMIZER:
                from .chain_optimizer import ChainOptimizerAgent

                agent = ChainOptimizerAgent(self.langgraph_url)
                result = await agent.execute(task.operation, task.input_data)

            else:
                raise ValueError(f"Unknown agent type: {task.agent_type}")

            # Success
            task.result = result
            task.completed_at = datetime.utcnow()

            # Update statistics
            agent_status.tasks_completed += 1
            execution_time = (task.completed_at - task.created_at).total_seconds()
            agent_status.avg_execution_time = (
                (agent_status.avg_execution_time * (agent_status.tasks_completed - 1) + execution_time)
                / agent_status.tasks_completed
            )

            logger.info(f"Task {task_id} completed successfully in {execution_time:.2f}s")
            return result

        except Exception as e:
            task.error = str(e)
            task.completed_at = datetime.utcnow()
            agent_status.tasks_failed += 1
            logger.error(f"Task {task_id} failed: {e}")
            raise

        finally:
            # Cleanup
            agent_status.is_active = False
            agent_status.current_task = None
            del self.active_tasks[task_id]
            self.completed_tasks[task_id] = task
            self.total_tasks_completed += 1

    async def get_task_result(self, task_id: str, wait: bool = True, timeout: float = 300.0) -> Optional[Any]:
        """Get result of a task, optionally waiting for completion"""
        if task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
            if task.error:
                raise Exception(task.error)
            return task.result

        if not wait:
            return None

        # Wait for task to complete
        start_time = datetime.utcnow()
        while (datetime.utcnow() - start_time).total_seconds() < timeout:
            if task_id in self.completed_tasks:
                task = self.completed_tasks[task_id]
                if task.error:
                    raise Exception(task.error)
                return task.result
            await asyncio.sleep(0.5)

        raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")

    async def consensus_decision(
        self,
        question: str,
        context: Dict[str, Any],
        agents: Optional[List[AgentType]] = None,
    ) -> Dict[str, Any]:
        """
        Get consensus decision from multiple agents.

        All specified agents analyze the question and context, then
        their responses are aggregated into a consensus.
        """
        agents = agents or list(AgentType)

        # Delegate to all agents in parallel
        tasks = [
            (agent_type, "analyze", {"question": question, "context": context})
            for agent_type in agents
        ]

        task_ids = await self.delegate_parallel(tasks, wait_for_all=True)

        # Collect results
        responses = {}
        for task_id in task_ids:
            try:
                result = await self.get_task_result(task_id, wait=True)
                task = self.completed_tasks[task_id]
                responses[task.agent_type.value] = result
            except Exception as e:
                logger.error(f"Failed to get response from task {task_id}: {e}")

        # Aggregate into consensus
        consensus = {
            "question": question,
            "responses": responses,
            "consensus_confidence": len(responses) / len(agents),
            "participating_agents": list(responses.keys()),
        }

        return consensus

    def get_agent_status(self, agent_type: Optional[AgentType] = None) -> Dict[str, Any]:
        """Get status of one or all agents"""
        if agent_type:
            status = self.agents[agent_type]
            return {
                "agent_type": status.agent_type.value,
                "is_active": status.is_active,
                "current_task": status.current_task,
                "tasks_completed": status.tasks_completed,
                "tasks_failed": status.tasks_failed,
                "avg_execution_time": status.avg_execution_time,
                "last_active": status.last_active.isoformat() if status.last_active else None,
            }

        return {
            agent_type.value: self.get_agent_status(agent_type)
            for agent_type in AgentType
        }

    def get_coordinator_stats(self) -> Dict[str, Any]:
        """Get overall coordinator statistics"""
        return {
            "total_tasks_delegated": self.total_tasks_delegated,
            "total_tasks_completed": self.total_tasks_completed,
            "queue_size": len(self.task_queue),
            "active_tasks": len(self.active_tasks),
            "agents": self.get_agent_status(),
        }
