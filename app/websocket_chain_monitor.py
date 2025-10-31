"""WebSocket chain execution monitoring for real-time updates."""

import asyncio
import json
from typing import Optional, Dict, List, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from .logger import logger
from .database import SessionLocal
from . import crud


class ChainExecutionMonitor:
    """Monitor chain execution and broadcast updates via WebSocket."""

    def __init__(self):
        # Track active WebSocket connections per execution_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Track monitoring tasks
        self.monitor_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, execution_id: str):
        """Connect WebSocket client for a specific execution."""
        await websocket.accept()

        if execution_id not in self.active_connections:
            self.active_connections[execution_id] = set()

        self.active_connections[execution_id].add(websocket)
        logger.info(f"WebSocket connected for execution: {execution_id} (total: {len(self.active_connections[execution_id])})")

    def disconnect(self, websocket: WebSocket, execution_id: str):
        """Disconnect WebSocket client."""
        if execution_id in self.active_connections:
            if websocket in self.active_connections[execution_id]:
                self.active_connections[execution_id].remove(websocket)

            # Clean up if no more connections
            if not self.active_connections[execution_id]:
                del self.active_connections[execution_id]
                logger.info(f"No more connections for execution: {execution_id}")

                # Cancel monitoring task if exists
                if execution_id in self.monitor_tasks:
                    self.monitor_tasks[execution_id].cancel()
                    del self.monitor_tasks[execution_id]
            else:
                logger.info(f"WebSocket disconnected for execution: {execution_id} (remaining: {len(self.active_connections[execution_id])})")

    async def broadcast(self, execution_id: str, message: dict):
        """Broadcast message to all connected clients for an execution."""
        if execution_id not in self.active_connections:
            return

        # Create list to track disconnected websockets
        disconnected = []

        for websocket in self.active_connections[execution_id]:
            try:
                await websocket.send_json(message)
            except WebSocketDisconnect:
                logger.info(f"Client disconnected during broadcast: {execution_id}")
                disconnected.append(websocket)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(websocket)

        # Remove disconnected websockets
        for websocket in disconnected:
            self.disconnect(websocket, execution_id)

    async def send_execution_update(self, execution_id: str, db: Session):
        """Send execution status update to all connected clients."""
        try:
            # Get current execution state from database
            execution = crud.get_chain_execution_by_id(db, execution_id)
            if not execution:
                logger.warning(f"Execution not found: {execution_id}")
                return

            # Parse results
            results = []
            if execution.results:
                try:
                    results = json.loads(execution.results)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse results for execution: {execution_id}")

            message = {
                "type": "execution_update",
                "data": {
                    "execution_id": execution.execution_id,
                    "chain_id": execution.chain_id,
                    "chain_name": execution.chain_name,
                    "status": execution.status,
                    "total_steps": execution.total_steps,
                    "completed_steps": execution.completed_steps,
                    "failed_steps": execution.failed_steps,
                    "skipped_steps": execution.skipped_steps,
                    "start_time": execution.start_time.isoformat() if execution.start_time else None,
                    "end_time": execution.end_time.isoformat() if execution.end_time else None,
                    "duration": execution.duration,
                    "error_message": execution.error_message,
                }
            }

            await self.broadcast(execution_id, message)

        except Exception as e:
            logger.error(f"Error sending execution update: {e}", exc_info=True)

    async def send_step_start(
        self,
        execution_id: str,
        step_index: int,
        step_name: str,
        tool: str,
        start_time: datetime
    ):
        """Notify clients that a step has started."""
        message = {
            "type": "step_start",
            "data": {
                "step_index": step_index,
                "step_name": step_name,
                "tool": tool,
                "start_time": start_time.isoformat() if start_time else None,
            }
        }

        await self.broadcast(execution_id, message)
        logger.info(f"Step started: {execution_id} - Step {step_index}: {step_name}")

    async def send_step_complete(
        self,
        execution_id: str,
        step_index: int,
        end_time: datetime,
        duration: float,
        output: Optional[List[str]] = None
    ):
        """Notify clients that a step has completed successfully."""
        message = {
            "type": "step_complete",
            "data": {
                "step_index": step_index,
                "end_time": end_time.isoformat() if end_time else None,
                "duration": duration,
                "output": output or []
            }
        }

        await self.broadcast(execution_id, message)
        logger.info(f"Step completed: {execution_id} - Step {step_index}")

    async def send_step_failed(
        self,
        execution_id: str,
        step_index: int,
        end_time: datetime,
        duration: float,
        error: str,
        output: Optional[List[str]] = None
    ):
        """Notify clients that a step has failed."""
        message = {
            "type": "step_failed",
            "data": {
                "step_index": step_index,
                "end_time": end_time.isoformat() if end_time else None,
                "duration": duration,
                "error": error,
                "output": output or []
            }
        }

        await self.broadcast(execution_id, message)
        logger.warning(f"Step failed: {execution_id} - Step {step_index}: {error}")

    async def send_execution_complete(
        self,
        execution_id: str,
        end_time: datetime,
        duration: float
    ):
        """Notify clients that execution has completed successfully."""
        message = {
            "type": "execution_complete",
            "data": {
                "end_time": end_time.isoformat() if end_time else None,
                "duration": duration,
            }
        }

        await self.broadcast(execution_id, message)
        logger.info(f"Execution completed: {execution_id}")

    async def send_execution_failed(
        self,
        execution_id: str,
        end_time: datetime,
        duration: float,
        error: str
    ):
        """Notify clients that execution has failed."""
        message = {
            "type": "execution_failed",
            "data": {
                "end_time": end_time.isoformat() if end_time else None,
                "duration": duration,
                "error": error,
            }
        }

        await self.broadcast(execution_id, message)
        logger.error(f"Execution failed: {execution_id} - {error}")

    async def send_error(self, execution_id: str, error_message: str):
        """Send error message to clients."""
        message = {
            "type": "error",
            "data": {
                "message": error_message,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        await self.broadcast(execution_id, message)

    async def monitor_execution(self, execution_id: str, websocket: WebSocket):
        """Monitor execution and send periodic updates."""
        db = SessionLocal()
        try:
            # Send initial execution state
            await self.send_execution_update(execution_id, db)

            # Poll for updates while execution is active
            while True:
                try:
                    # Get current execution state
                    execution = crud.get_chain_execution_by_id(db, execution_id)
                    if not execution:
                        logger.warning(f"Execution not found: {execution_id}")
                        await self.send_error(execution_id, "Execution not found")
                        break

                    # Send periodic update
                    await self.send_execution_update(execution_id, db)

                    # Check if execution is complete
                    if execution.status in ["completed", "failed", "cancelled"]:
                        logger.info(f"Execution monitoring complete: {execution_id} (status: {execution.status})")
                        break

                    # Send keepalive ping
                    await self.broadcast(execution_id, {"type": "ping"})

                    # Wait before next poll
                    await asyncio.sleep(2)  # Poll every 2 seconds

                except asyncio.CancelledError:
                    logger.info(f"Monitoring cancelled for execution: {execution_id}")
                    break
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                    await asyncio.sleep(5)  # Wait longer on error

        except Exception as e:
            logger.error(f"Fatal error monitoring execution: {e}", exc_info=True)
            await self.send_error(execution_id, f"Monitoring error: {str(e)}")
        finally:
            db.close()

    async def start_monitoring(self, execution_id: str, websocket: WebSocket):
        """Start monitoring task for an execution."""
        # Cancel existing task if any
        if execution_id in self.monitor_tasks:
            self.monitor_tasks[execution_id].cancel()

        # Create new monitoring task
        task = asyncio.create_task(self.monitor_execution(execution_id, websocket))
        self.monitor_tasks[execution_id] = task

        logger.info(f"Started monitoring for execution: {execution_id}")

    async def handle_client_message(self, execution_id: str, message: dict):
        """Handle incoming client messages."""
        msg_type = message.get("type")

        if msg_type == "pong":
            # Keepalive response
            pass
        elif msg_type == "subscribe":
            # Client wants to subscribe to updates (already handled by connect)
            pass
        else:
            logger.warning(f"Unknown message type from client: {msg_type}")


# Global instance
chain_monitor = ChainExecutionMonitor()
