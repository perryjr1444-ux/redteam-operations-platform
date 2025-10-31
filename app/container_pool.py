"""
Distributed Container Pool Manager - Fractal Parallelism at Container Level

Manages a dynamic pool of Kali Linux containers for parallel attack execution.
Implements:
- Pre-warming: Pre-spawn containers for instant availability
- Pool management: Dynamic scaling based on demand
- Load balancing: Distribute work across available containers
- Health monitoring: Auto-recovery and replacement of failed containers
- Resource limits: CPU/memory quotas per container

Part of the fractal execution framework - Layer 5: Container Parallelism
"""

import asyncio
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ContainerStatus(str, Enum):
    """Container lifecycle status"""
    CREATING = "creating"
    READY = "ready"
    BUSY = "busy"
    UNHEALTHY = "unhealthy"
    TERMINATING = "terminating"


@dataclass
class ContainerInfo:
    """Information about a container in the pool"""
    id: str
    name: str
    status: ContainerStatus
    image: str
    created_at: datetime
    last_used: Optional[datetime] = None
    current_task: Optional[str] = None
    health_checks_failed: int = 0
    tasks_completed: int = 0
    cpu_limit: str = "1.0"
    memory_limit: str = "1G"


class ContainerPool:
    """
    Manages a pool of Kali Linux containers for parallel execution.

    Implements fractal parallelism by maintaining a ready pool of containers
    that can execute attack tools concurrently.
    """

    def __init__(
        self,
        min_size: int = 3,
        max_size: int = 20,
        prewarm_count: int = 5,
        image: str = "kalilinux/kali-rolling:latest",
        podman_service=None,
    ):
        self.min_size = min_size
        self.max_size = max_size
        self.prewarm_count = prewarm_count
        self.image = image
        self.podman_service = podman_service

        # Pool state
        self.containers: Dict[str, ContainerInfo] = {}
        self.ready_queue: asyncio.Queue = asyncio.Queue()
        self.pool_initialized = False

        # Statistics
        self.total_containers_created = 0
        self.total_containers_terminated = 0
        self.total_tasks_executed = 0

        logger.info(f"Container pool initialized (min={min_size}, max={max_size}, prewarm={prewarm_count})")

    async def initialize(self):
        """Initialize the container pool with pre-warmed containers"""
        if self.pool_initialized:
            logger.warning("Pool already initialized")
            return

        logger.info(f"Initializing container pool with {self.prewarm_count} pre-warmed containers...")

        # Create pre-warmed containers
        create_tasks = [
            self._create_container(f"pool-{i}")
            for i in range(self.prewarm_count)
        ]
        await asyncio.gather(*create_tasks)

        self.pool_initialized = True
        logger.info(f"Container pool ready with {len(self.containers)} containers")

    async def _create_container(self, name: str) -> str:
        """Create a new container and add it to the pool"""
        container_id = f"container_{self.total_containers_created}_{name}"

        container = ContainerInfo(
            id=container_id,
            name=name,
            status=ContainerStatus.CREATING,
            image=self.image,
            created_at=datetime.utcnow(),
        )

        self.containers[container_id] = container
        self.total_containers_created += 1

        try:
            # Use podman service to create container
            if self.podman_service:
                # In production, would call: await self.podman_service.create_container(...)
                pass

            # Simulate container creation
            await asyncio.sleep(0.1)

            # Mark as ready and add to queue
            container.status = ContainerStatus.READY
            await self.ready_queue.put(container_id)

            logger.info(f"Container created and ready: {container_id}")
            return container_id

        except Exception as e:
            logger.error(f"Failed to create container {container_id}: {e}")
            container.status = ContainerStatus.UNHEALTHY
            raise

    async def acquire(self, task_id: Optional[str] = None, timeout: float = 60.0) -> Optional[str]:
        """
        Acquire a container from the pool for task execution.

        Returns: Container ID, or None if timeout
        """
        try:
            # Try to get from ready queue
            container_id = await asyncio.wait_for(
                self.ready_queue.get(),
                timeout=timeout,
            )

            container = self.containers.get(container_id)
            if not container:
                logger.error(f"Container {container_id} not found in pool")
                return None

            # Mark as busy
            container.status = ContainerStatus.BUSY
            container.current_task = task_id
            container.last_used = datetime.utcnow()

            logger.info(f"Container acquired: {container_id} for task {task_id}")
            return container_id

        except asyncio.TimeoutError:
            logger.warning(f"Timeout acquiring container after {timeout}s")

            # Try to scale up if under max
            if len(self.containers) < self.max_size:
                logger.info("Attempting to scale up pool...")
                new_container_id = await self._create_container(f"scale-{self.total_containers_created}")
                return await self.acquire(task_id, timeout=10.0)

            return None

    async def release(self, container_id: str, healthy: bool = True):
        """Release a container back to the pool"""
        container = self.containers.get(container_id)
        if not container:
            logger.error(f"Cannot release unknown container: {container_id}")
            return

        container.current_task = None
        container.tasks_completed += 1
        self.total_tasks_executed += 1

        if healthy:
            # Return to ready queue
            container.status = ContainerStatus.READY
            await self.ready_queue.put(container_id)
            logger.info(f"Container released: {container_id} (tasks completed: {container.tasks_completed})")
        else:
            # Mark unhealthy and replace
            container.status = ContainerStatus.UNHEALTHY
            container.health_checks_failed += 1
            logger.warning(f"Container marked unhealthy: {container_id}")

            # Replace with new container
            if len(self.containers) >= self.min_size:
                await self._terminate_container(container_id)
            await self._create_container(f"replacement-{self.total_containers_created}")

    async def _terminate_container(self, container_id: str):
        """Terminate and remove a container from the pool"""
        container = self.containers.get(container_id)
        if not container:
            return

        container.status = ContainerStatus.TERMINATING

        try:
            # Use podman service to terminate
            if self.podman_service:
                # await self.podman_service.terminate_container(container_id)
                pass

            # Simulate termination
            await asyncio.sleep(0.1)

            del self.containers[container_id]
            self.total_containers_terminated += 1

            logger.info(f"Container terminated: {container_id}")

        except Exception as e:
            logger.error(f"Error terminating container {container_id}: {e}")

    async def execute_parallel(
        self,
        tasks: List[Dict[str, any]],
        executor_func: callable,
    ) -> List[any]:
        """
        Execute multiple tasks in parallel using pool containers.

        This is the key method for fractal parallelism at the container level.
        """
        logger.info(f"Executing {len(tasks)} tasks in parallel across container pool")

        async def execute_task(task):
            container_id = None
            try:
                # Acquire container
                container_id = await self.acquire(task.get("id"))
                if not container_id:
                    raise Exception("Failed to acquire container")

                # Execute task
                result = await executor_func(container_id, task)
                return result

            except Exception as e:
                logger.error(f"Task failed: {e}")
                raise

            finally:
                # Release container
                if container_id:
                    await self.release(container_id, healthy=True)

        # Execute all tasks in parallel
        results = await asyncio.gather(
            *[execute_task(task) for task in tasks],
            return_exceptions=True,
        )

        return results

    async def scale_to(self, target_size: int):
        """Scale pool to target size"""
        current_size = len(self.containers)

        if target_size > self.max_size:
            target_size = self.max_size
            logger.warning(f"Target size capped at max_size: {self.max_size}")

        if target_size < self.min_size:
            target_size = self.min_size
            logger.warning(f"Target size raised to min_size: {self.min_size}")

        if target_size > current_size:
            # Scale up
            to_create = target_size - current_size
            logger.info(f"Scaling up pool by {to_create} containers")
            create_tasks = [
                self._create_container(f"scale-{i}")
                for i in range(to_create)
            ]
            await asyncio.gather(*create_tasks)

        elif target_size < current_size:
            # Scale down (terminate idle containers)
            to_remove = current_size - target_size
            logger.info(f"Scaling down pool by {to_remove} containers")

            idle_containers = [
                cid for cid, c in self.containers.items()
                if c.status == ContainerStatus.READY
            ][:to_remove]

            for container_id in idle_containers:
                await self._terminate_container(container_id)

    def get_pool_stats(self) -> Dict[str, any]:
        """Get pool statistics"""
        status_counts = {}
        for container in self.containers.values():
            status_counts[container.status.value] = status_counts.get(container.status.value, 0) + 1

        return {
            "total_containers": len(self.containers),
            "ready_containers": status_counts.get("ready", 0),
            "busy_containers": status_counts.get("busy", 0),
            "unhealthy_containers": status_counts.get("unhealthy", 0),
            "total_created": self.total_containers_created,
            "total_terminated": self.total_containers_terminated,
            "total_tasks_executed": self.total_tasks_executed,
            "min_size": self.min_size,
            "max_size": self.max_size,
        }

    async def health_check(self):
        """Perform health checks on all containers"""
        logger.info("Running container pool health check...")

        for container_id, container in list(self.containers.items()):
            try:
                # Health check logic
                if container.status == ContainerStatus.UNHEALTHY:
                    if container.health_checks_failed >= 3:
                        await self._terminate_container(container_id)
                        await self._create_container(f"health-replacement-{self.total_containers_created}")
            except Exception as e:
                logger.error(f"Health check failed for {container_id}: {e}")

        logger.info("Health check complete")

    async def shutdown(self):
        """Gracefully shutdown the container pool"""
        logger.info("Shutting down container pool...")

        # Terminate all containers
        terminate_tasks = [
            self._terminate_container(container_id)
            for container_id in list(self.containers.keys())
        ]
        await asyncio.gather(*terminate_tasks, return_exceptions=True)

        logger.info("Container pool shutdown complete")
