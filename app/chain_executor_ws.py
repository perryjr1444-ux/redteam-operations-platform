"""
Chain Executor with WebSocket Integration
Executes attack chains with real-time WebSocket progress updates.
"""

import asyncio
from typing import Optional, Dict, List, Any
from datetime import datetime
from sqlalchemy.orm import Session
import json

from .logger import logger
from .websocket_chain_monitor import chain_monitor
from . import crud


class ChainExecutorWithWebSocket:
    """
    Execute attack chains with real-time WebSocket updates.

    This class wraps chain execution logic and emits WebSocket events
    for each step of the execution process.
    """

    def __init__(self, db: Session):
        self.db = db

    async def execute_chain(
        self,
        execution_id: str,
        chain_id: str,
        steps: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute attack chain with WebSocket progress updates.

        Args:
            execution_id: Unique execution identifier
            chain_id: Chain being executed
            steps: List of chain steps to execute
            context: Optional execution context (target info, etc.)

        Returns:
            Execution result summary
        """
        logger.info(f"Starting chain execution: {execution_id} for chain: {chain_id}")

        start_time = datetime.utcnow()
        results = []
        completed_steps = 0
        failed_steps = 0
        skipped_steps = 0

        try:
            # Update execution status to running
            crud.update_chain_execution(self.db, execution_id, {
                "status": "running",
                "start_time": start_time
            })

            # Send initial update
            await chain_monitor.send_execution_update(execution_id, self.db)

            # Execute each step
            for step_index, step in enumerate(steps):
                step_name = step.get("name", f"Step {step_index + 1}")
                tool = step.get("tool", "unknown")

                # Skip if step has skip condition
                if step.get("skip", False):
                    logger.info(f"Skipping step {step_index}: {step_name}")
                    skipped_steps += 1

                    results.append({
                        "step_index": step_index,
                        "step_name": step_name,
                        "status": "skipped",
                        "reason": step.get("skip_reason", "Conditional skip")
                    })

                    continue

                # Execute step
                step_result = await self._execute_step(
                    execution_id=execution_id,
                    step_index=step_index,
                    step=step,
                    context=context
                )

                results.append(step_result)

                # Update counters
                if step_result["status"] == "completed":
                    completed_steps += 1
                elif step_result["status"] == "failed":
                    failed_steps += 1

                    # Check if we should stop on failure
                    if step.get("stop_on_failure", False):
                        logger.warning(f"Stopping execution due to step failure: {step_name}")
                        break

                # Update execution progress
                crud.update_chain_execution(self.db, execution_id, {
                    "completed_steps": completed_steps,
                    "failed_steps": failed_steps,
                    "skipped_steps": skipped_steps,
                    "results": results
                })

                # Brief delay between steps
                await asyncio.sleep(0.5)

            # Determine final status
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            if failed_steps > 0 and completed_steps == 0:
                final_status = "failed"
                error_message = f"{failed_steps} steps failed"
            elif failed_steps > 0:
                final_status = "completed_with_errors"
                error_message = f"{failed_steps} of {len(steps)} steps failed"
            else:
                final_status = "completed"
                error_message = None

            # Update execution record
            crud.update_chain_execution(self.db, execution_id, {
                "status": final_status,
                "end_time": end_time,
                "duration": duration,
                "completed_steps": completed_steps,
                "failed_steps": failed_steps,
                "skipped_steps": skipped_steps,
                "results": results,
                "error_message": error_message
            })

            # Send completion notification
            if final_status == "completed":
                await chain_monitor.send_execution_complete(
                    execution_id=execution_id,
                    end_time=end_time,
                    duration=duration
                )
            else:
                await chain_monitor.send_execution_failed(
                    execution_id=execution_id,
                    end_time=end_time,
                    duration=duration,
                    error=error_message or "Execution failed"
                )

            logger.info(f"Chain execution complete: {execution_id} - Status: {final_status}")

            return {
                "success": final_status in ["completed", "completed_with_errors"],
                "status": final_status,
                "completed_steps": completed_steps,
                "failed_steps": failed_steps,
                "skipped_steps": skipped_steps,
                "duration": duration,
                "results": results
            }

        except Exception as e:
            logger.error(f"Error executing chain {execution_id}: {e}", exc_info=True)

            # Update execution record with error
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            crud.update_chain_execution(self.db, execution_id, {
                "status": "failed",
                "end_time": end_time,
                "duration": duration,
                "error_message": str(e),
                "results": results
            })

            # Send failure notification
            await chain_monitor.send_execution_failed(
                execution_id=execution_id,
                end_time=end_time,
                duration=duration,
                error=str(e)
            )

            return {
                "success": False,
                "status": "failed",
                "error": str(e),
                "completed_steps": completed_steps,
                "failed_steps": failed_steps,
                "skipped_steps": skipped_steps,
                "duration": duration,
                "results": results
            }

    async def _execute_step(
        self,
        execution_id: str,
        step_index: int,
        step: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a single chain step with WebSocket updates.

        Args:
            execution_id: Execution identifier
            step_index: Index of the step
            step: Step definition
            context: Execution context

        Returns:
            Step execution result
        """
        step_name = step.get("name", f"Step {step_index + 1}")
        tool = step.get("tool", "unknown")
        params = step.get("params", {})
        timeout = step.get("timeout", 300)  # Default 5 minutes

        logger.info(f"Executing step {step_index}: {step_name} (tool: {tool})")

        step_start = datetime.utcnow()

        # Send step start notification
        await chain_monitor.send_step_start(
            execution_id=execution_id,
            step_index=step_index,
            step_name=step_name,
            tool=tool,
            start_time=step_start
        )

        try:
            # Execute the step (this would call actual tool execution)
            # For now, this is a placeholder that simulates execution
            output = await self._simulate_step_execution(
                tool=tool,
                params=params,
                timeout=timeout
            )

            step_end = datetime.utcnow()
            step_duration = (step_end - step_start).total_seconds()

            # Send step completion notification
            await chain_monitor.send_step_complete(
                execution_id=execution_id,
                step_index=step_index,
                end_time=step_end,
                duration=step_duration,
                output=output
            )

            return {
                "step_index": step_index,
                "step_name": step_name,
                "tool": tool,
                "status": "completed",
                "start_time": step_start.isoformat(),
                "end_time": step_end.isoformat(),
                "duration": step_duration,
                "output": output
            }

        except asyncio.TimeoutError:
            step_end = datetime.utcnow()
            step_duration = (step_end - step_start).total_seconds()
            error_msg = f"Step timed out after {timeout} seconds"

            logger.error(f"Step {step_index} timed out: {step_name}")

            # Send step failure notification
            await chain_monitor.send_step_failed(
                execution_id=execution_id,
                step_index=step_index,
                end_time=step_end,
                duration=step_duration,
                error=error_msg,
                output=[]
            )

            return {
                "step_index": step_index,
                "step_name": step_name,
                "tool": tool,
                "status": "failed",
                "start_time": step_start.isoformat(),
                "end_time": step_end.isoformat(),
                "duration": step_duration,
                "error": error_msg
            }

        except Exception as e:
            step_end = datetime.utcnow()
            step_duration = (step_end - step_start).total_seconds()
            error_msg = str(e)

            logger.error(f"Step {step_index} failed: {step_name} - {error_msg}", exc_info=True)

            # Send step failure notification
            await chain_monitor.send_step_failed(
                execution_id=execution_id,
                step_index=step_index,
                end_time=step_end,
                duration=step_duration,
                error=error_msg,
                output=[]
            )

            return {
                "step_index": step_index,
                "step_name": step_name,
                "tool": tool,
                "status": "failed",
                "start_time": step_start.isoformat(),
                "end_time": step_end.isoformat(),
                "duration": step_duration,
                "error": error_msg
            }

    async def _simulate_step_execution(
        self,
        tool: str,
        params: Dict[str, Any],
        timeout: int
    ) -> List[str]:
        """
        Simulate step execution (placeholder for actual tool execution).

        In production, this would:
        1. Acquire a container from the pool
        2. Execute the tool with given params
        3. Collect output
        4. Return container to pool

        Args:
            tool: Tool to execute
            params: Tool parameters
            timeout: Execution timeout

        Returns:
            List of output lines
        """
        # Simulate execution delay
        await asyncio.sleep(1)

        # Return mock output
        return [
            f"Executing {tool} with params: {params}",
            f"Tool execution started at {datetime.utcnow().isoformat()}",
            "Processing...",
            f"Tool execution completed successfully"
        ]


async def execute_chain_async(
    db: Session,
    execution_id: str,
    chain_id: str,
    steps: List[Dict[str, Any]],
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function to execute a chain asynchronously with WebSocket updates.

    Args:
        db: Database session
        execution_id: Execution identifier
        chain_id: Chain identifier
        steps: List of chain steps
        context: Execution context

    Returns:
        Execution result
    """
    executor = ChainExecutorWithWebSocket(db)
    return await executor.execute_chain(
        execution_id=execution_id,
        chain_id=chain_id,
        steps=steps,
        context=context
    )
