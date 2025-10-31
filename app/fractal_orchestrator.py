"""
Fractal Orchestration Framework
Multi-level parallel execution engine for autonomous red team operations.

Implements fractal parallelism at 5 layers:
1. Meta-Orchestrator: Coordinates AI agents
2. Exercise Level: Multiple exercises in parallel
3. Chain Level: Parallel attack chains
4. Tool Level: Concurrent tool execution
5. Container Level: Distributed container pool

Author: Autonomous Agent System
Version: 1.0.0
"""

import asyncio
from typing import List, Dict, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ExecutionLevel(str, Enum):
    """Levels of fractal execution"""
    META = "meta"  # AI agent coordination
    EXERCISE = "exercise"  # Exercise parallelism
    CHAIN = "chain"  # Attack chain parallelism
    TOOL = "tool"  # Tool execution parallelism
    CONTAINER = "container"  # Container resource parallelism


class ExecutionStatus(str, Enum):
    """Status of execution at any level"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionNode:
    """A node in the fractal execution tree"""
    id: str
    level: ExecutionLevel
    type: str  # "agent", "exercise", "chain", "tool", "container"
    name: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    def duration(self) -> Optional[float]:
        """Calculate execution duration"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


@dataclass
class ResourcePool:
    """Manages resource allocation across execution levels"""
    max_concurrent_exercises: int = 5
    max_concurrent_chains: int = 10
    max_concurrent_tools: int = 20
    max_containers: int = 50

    # Current usage
    active_exercises: int = 0
    active_chains: int = 0
    active_tools: int = 0
    active_containers: int = 0

    def can_allocate(self, level: ExecutionLevel) -> bool:
        """Check if resources available for this level"""
        if level == ExecutionLevel.EXERCISE:
            return self.active_exercises < self.max_concurrent_exercises
        elif level == ExecutionLevel.CHAIN:
            return self.active_chains < self.max_concurrent_chains
        elif level == ExecutionLevel.TOOL:
            return self.active_tools < self.max_concurrent_tools
        elif level == ExecutionLevel.CONTAINER:
            return self.active_containers < self.max_containers
        return True

    def allocate(self, level: ExecutionLevel):
        """Allocate resources for this level"""
        if level == ExecutionLevel.EXERCISE:
            self.active_exercises += 1
        elif level == ExecutionLevel.CHAIN:
            self.active_chains += 1
        elif level == ExecutionLevel.TOOL:
            self.active_tools += 1
        elif level == ExecutionLevel.CONTAINER:
            self.active_containers += 1

    def release(self, level: ExecutionLevel):
        """Release resources for this level"""
        if level == ExecutionLevel.EXERCISE:
            self.active_exercises = max(0, self.active_exercises - 1)
        elif level == ExecutionLevel.CHAIN:
            self.active_chains = max(0, self.active_chains - 1)
        elif level == ExecutionLevel.TOOL:
            self.active_tools = max(0, self.active_tools - 1)
        elif level == ExecutionLevel.CONTAINER:
            self.active_containers = max(0, self.active_containers - 1)


class FractalOrchestrator:
    """
    Main fractal orchestration engine.

    Manages parallel execution at all architectural levels with intelligent
    resource allocation, dependency resolution, and error handling.
    """

    def __init__(self, resource_pool: Optional[ResourcePool] = None):
        self.nodes: Dict[str, ExecutionNode] = {}
        self.execution_tree: Dict[str, List[str]] = defaultdict(list)  # parent -> children
        self.resource_pool = resource_pool or ResourcePool()
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.event_callbacks: Dict[str, List[Callable]] = defaultdict(list)

    def register_node(self, node: ExecutionNode):
        """Register an execution node in the tree"""
        self.nodes[node.id] = node
        if node.parent_id:
            self.execution_tree[node.parent_id].append(node.id)
        logger.info(f"Registered node: {node.id} (level: {node.level}, type: {node.type})")

    def get_node(self, node_id: str) -> Optional[ExecutionNode]:
        """Get node by ID"""
        return self.nodes.get(node_id)

    def get_children(self, node_id: str) -> List[ExecutionNode]:
        """Get all child nodes"""
        child_ids = self.execution_tree.get(node_id, [])
        return [self.nodes[cid] for cid in child_ids if cid in self.nodes]

    def get_ready_nodes(self) -> List[ExecutionNode]:
        """Get all nodes ready to execute (dependencies satisfied)"""
        ready = []
        for node in self.nodes.values():
            if node.status == ExecutionStatus.PENDING:
                # Check if dependencies are satisfied
                deps_satisfied = all(
                    self.nodes.get(dep_id, ExecutionNode("", ExecutionLevel.META, "", "")).status
                    == ExecutionStatus.COMPLETED
                    for dep_id in node.dependencies
                )
                if deps_satisfied and self.resource_pool.can_allocate(node.level):
                    ready.append(node)
        return ready

    async def execute_node(
        self,
        node_id: str,
        executor_func: Callable[[ExecutionNode], Any],
        on_complete: Optional[Callable] = None,
    ):
        """Execute a single node with the provided executor function"""
        node = self.nodes.get(node_id)
        if not node:
            logger.error(f"Node not found: {node_id}")
            return

        try:
            # Allocate resources
            self.resource_pool.allocate(node.level)

            # Update status
            node.status = ExecutionStatus.RUNNING
            node.start_time = datetime.utcnow()
            await self._emit_event("node_started", node)

            logger.info(f"Executing node: {node.id} ({node.level}/{node.type})")

            # Execute
            if asyncio.iscoroutinefunction(executor_func):
                result = await executor_func(node)
            else:
                result = executor_func(node)

            # Success
            node.result = result
            node.status = ExecutionStatus.COMPLETED
            node.end_time = datetime.utcnow()

            logger.info(f"Completed node: {node.id} ({node.duration():.2f}s)")
            await self._emit_event("node_completed", node)

            if on_complete:
                await on_complete(node)

        except Exception as e:
            # Failure
            node.status = ExecutionStatus.FAILED
            node.error = str(e)
            node.end_time = datetime.utcnow()
            logger.error(f"Failed node: {node.id} - {e}")
            await self._emit_event("node_failed", node)

        finally:
            # Release resources
            self.resource_pool.release(node.level)

    async def execute_fractal(
        self,
        root_node_id: str,
        level_executors: Dict[ExecutionLevel, Callable],
        max_parallel: int = 10,
    ) -> Dict[str, Any]:
        """
        Execute the entire fractal tree starting from root.

        Args:
            root_node_id: ID of the root node to start execution
            level_executors: Map of execution level to executor function
            max_parallel: Maximum parallel tasks at any level

        Returns:
            Execution summary with results and statistics
        """
        logger.info(f"Starting fractal execution from root: {root_node_id}")
        start_time = datetime.utcnow()

        # Queue for BFS traversal
        pending_nodes = {root_node_id}
        completed_nodes = set()
        failed_nodes = set()

        while pending_nodes or self.running_tasks:
            # Get ready nodes (dependencies satisfied, resources available)
            ready_nodes = [
                self.nodes[nid] for nid in pending_nodes
                if all(dep_id in completed_nodes for dep_id in self.nodes[nid].dependencies)
                and self.resource_pool.can_allocate(self.nodes[nid].level)
            ]

            # Limit parallelism
            if len(self.running_tasks) >= max_parallel:
                ready_nodes = []

            # Start execution for ready nodes
            for node in ready_nodes[:max_parallel - len(self.running_tasks)]:
                pending_nodes.remove(node.id)

                # Get appropriate executor for this level
                executor = level_executors.get(node.level)
                if not executor:
                    logger.warning(f"No executor for level {node.level}, skipping node {node.id}")
                    continue

                # Create task
                task = asyncio.create_task(self.execute_node(node.id, executor))
                self.running_tasks[node.id] = task

            # Wait for at least one task to complete
            if self.running_tasks:
                done, _ = await asyncio.wait(
                    self.running_tasks.values(),
                    return_when=asyncio.FIRST_COMPLETED,
                    timeout=1.0,
                )

                # Process completed tasks
                for task in done:
                    # Find node ID for this task
                    node_id = next(
                        (nid for nid, t in self.running_tasks.items() if t == task),
                        None,
                    )
                    if node_id:
                        del self.running_tasks[node_id]
                        node = self.nodes[node_id]

                        if node.status == ExecutionStatus.COMPLETED:
                            completed_nodes.add(node_id)
                            # Add children to pending
                            for child_id in self.execution_tree.get(node_id, []):
                                pending_nodes.add(child_id)
                        elif node.status == ExecutionStatus.FAILED:
                            failed_nodes.add(node_id)
            else:
                # Nothing running and nothing ready - wait a bit
                await asyncio.sleep(0.1)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Generate summary
        summary = {
            "root_node_id": root_node_id,
            "total_nodes": len(self.nodes),
            "completed": len(completed_nodes),
            "failed": len(failed_nodes),
            "duration": duration,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "nodes_by_level": self._get_stats_by_level(),
            "resource_usage": {
                "exercises": self.resource_pool.active_exercises,
                "chains": self.resource_pool.active_chains,
                "tools": self.resource_pool.active_tools,
                "containers": self.resource_pool.active_containers,
            },
        }

        logger.info(f"Fractal execution complete: {len(completed_nodes)} completed, {len(failed_nodes)} failed, {duration:.2f}s")
        return summary

    def _get_stats_by_level(self) -> Dict[str, Dict[str, int]]:
        """Get statistics grouped by execution level"""
        stats = defaultdict(lambda: {"total": 0, "completed": 0, "failed": 0, "pending": 0, "running": 0})
        for node in self.nodes.values():
            level = node.level.value
            stats[level]["total"] += 1
            if node.status == ExecutionStatus.COMPLETED:
                stats[level]["completed"] += 1
            elif node.status == ExecutionStatus.FAILED:
                stats[level]["failed"] += 1
            elif node.status == ExecutionStatus.PENDING:
                stats[level]["pending"] += 1
            elif node.status == ExecutionStatus.RUNNING:
                stats[level]["running"] += 1
        return dict(stats)

    async def _emit_event(self, event_type: str, node: ExecutionNode):
        """Emit event to registered callbacks"""
        for callback in self.event_callbacks.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(node)
                else:
                    callback(node)
            except Exception as e:
                logger.error(f"Error in event callback {event_type}: {e}")

    def on(self, event_type: str, callback: Callable):
        """Register event callback"""
        self.event_callbacks[event_type].append(callback)

    def get_execution_tree_visual(self) -> str:
        """Generate visual representation of execution tree"""
        lines = []

        def traverse(node_id: str, depth: int = 0):
            node = self.nodes.get(node_id)
            if not node:
                return

            indent = "  " * depth
            status_symbol = {
                ExecutionStatus.PENDING: "○",
                ExecutionStatus.RUNNING: "◐",
                ExecutionStatus.COMPLETED: "●",
                ExecutionStatus.FAILED: "✗",
                ExecutionStatus.CANCELLED: "⊗",
            }.get(node.status, "?")

            duration_str = f"({node.duration():.2f}s)" if node.duration() else ""
            lines.append(f"{indent}{status_symbol} [{node.level.value}] {node.name} {duration_str}")

            for child_id in self.execution_tree.get(node_id, []):
                traverse(child_id, depth + 1)

        # Find root nodes (no parent)
        roots = [nid for nid, node in self.nodes.items() if not node.parent_id]
        for root_id in roots:
            traverse(root_id)

        return "\n".join(lines)


# Example usage and factory functions
def create_exercise_node(exercise_id: str, exercise_name: str, parent_id: Optional[str] = None) -> ExecutionNode:
    """Factory function to create exercise-level node"""
    return ExecutionNode(
        id=f"exercise_{exercise_id}",
        level=ExecutionLevel.EXERCISE,
        type="exercise",
        name=exercise_name,
        parent_id=parent_id,
    )


def create_chain_node(chain_id: str, chain_name: str, exercise_id: str) -> ExecutionNode:
    """Factory function to create chain-level node"""
    return ExecutionNode(
        id=f"chain_{chain_id}",
        level=ExecutionLevel.CHAIN,
        type="chain",
        name=chain_name,
        parent_id=f"exercise_{exercise_id}",
    )


def create_tool_node(tool_id: str, tool_name: str, chain_id: str) -> ExecutionNode:
    """Factory function to create tool-level node"""
    return ExecutionNode(
        id=f"tool_{tool_id}",
        level=ExecutionLevel.TOOL,
        type="tool",
        name=tool_name,
        parent_id=f"chain_{chain_id}",
    )


def create_agent_node(agent_id: str, agent_type: str, parent_id: Optional[str] = None) -> ExecutionNode:
    """Factory function to create agent-level node"""
    return ExecutionNode(
        id=f"agent_{agent_id}",
        level=ExecutionLevel.META,
        type="agent",
        name=agent_type,
        parent_id=parent_id,
    )
