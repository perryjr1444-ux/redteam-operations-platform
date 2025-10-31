"""
WebSocket Server for Real-time Tool Execution Streaming
Enhanced with Fractal Execution Visualization Support
"""

import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set, Any, List
import json
from datetime import datetime

from app.tools import ToolExecutor, get_registry, AttackChainOrchestrator
from app.logger import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """Manage WebSocket connections for tool execution and fractal visualization"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.executor = ToolExecutor()
        self.registry = get_registry()
        self.orchestrator = AttackChainOrchestrator(self.executor, self.registry)

        # Fractal execution subscriptions
        self.execution_subscriptions: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        dead_connections = set()

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                dead_connections.add(connection)

        # Clean up dead connections
        self.active_connections -= dead_connections

    async def handle_message(self, websocket: WebSocket, data: dict):
        """
        Handle incoming WebSocket messages

        Message types:
        - execute_tool: Run a single tool
        - execute_chain: Run an attack chain
        - kill_execution: Stop a running execution
        - subscribe: Subscribe to fractal execution updates
        - unsubscribe: Unsubscribe from fractal execution updates
        - ping: Heartbeat ping
        """
        msg_type = data.get('type') or data.get('action')

        if msg_type == 'execute_tool':
            await self.execute_tool(websocket, data)
        elif msg_type == 'execute_chain':
            await self.execute_chain(websocket, data)
        elif msg_type == 'kill_execution':
            await self.kill_execution(data)
        elif msg_type == 'subscribe':
            execution_id = data.get('execution_id')
            if execution_id:
                await self.subscribe_to_execution(websocket, execution_id)
            else:
                await self.send_personal_message({
                    'type': 'error',
                    'data': 'Missing execution_id for subscribe'
                }, websocket)
        elif msg_type == 'unsubscribe':
            execution_id = data.get('execution_id')
            if execution_id:
                await self.unsubscribe_from_execution(websocket, execution_id)
            else:
                await self.send_personal_message({
                    'type': 'error',
                    'data': 'Missing execution_id for unsubscribe'
                }, websocket)
        elif msg_type == 'ping':
            await self.send_personal_message({
                'type': 'pong',
                'timestamp': datetime.utcnow().isoformat()
            }, websocket)
        else:
            await self.send_personal_message({
                'type': 'error',
                'data': f'Unknown message type: {msg_type}'
            }, websocket)

    async def execute_tool(self, websocket: WebSocket, data: dict):
        """Execute a single tool and stream output"""
        execution_id = data.get('execution_id')
        tool_name = data.get('tool')
        args = data.get('args', {})

        logger.info(f"Executing tool: {tool_name} ({execution_id})")

        # Build command
        try:
            command = self.registry.build_command(tool_name, args)
        except Exception as e:
            await self.send_personal_message({
                'type': 'tool_error',
                'execution_id': execution_id,
                'error': str(e)
            }, websocket)
            return

        # Execute and stream output
        try:
            async for output in self.executor.execute(command):
                # Send to requesting client
                await self.send_personal_message({
                    'type': 'tool_output',
                    'execution_id': execution_id,
                    'data': output
                }, websocket)

                # Broadcast to all clients
                await self.broadcast({
                    'type': 'tool_output',
                    'execution_id': execution_id,
                    'tool': tool_name,
                    'data': output
                })

                # Send completion message
                if output.get('type') == 'complete':
                    await self.send_personal_message({
                        'type': 'tool_complete',
                        'execution_id': execution_id,
                        'return_code': output.get('return_code'),
                        'duration': output.get('duration')
                    }, websocket)

        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            await self.send_personal_message({
                'type': 'tool_error',
                'execution_id': execution_id,
                'error': str(e)
            }, websocket)

    async def execute_chain(self, websocket: WebSocket, data: dict):
        """Execute an attack chain and stream progress"""
        execution_id = data.get('execution_id')
        chain_config = data.get('config')

        logger.info(f"Executing chain: {chain_config.get('name')} ({execution_id})")

        # Create chain
        from app.tools.chain import ChainDefinition, ChainStep

        steps = [
            ChainStep(**step_data) for step_data in chain_config.get('steps', [])
        ]

        chain = ChainDefinition(
            id=chain_config.get('id'),
            name=chain_config.get('name'),
            description=chain_config.get('description', ''),
            steps=steps
        )

        self.orchestrator.register_chain(chain)

        # Progress callback
        async def progress_callback(progress_data):
            await self.send_personal_message({
                'type': 'chain_progress',
                'execution_id': execution_id,
                **progress_data
            }, websocket)

            await self.broadcast({
                'type': 'chain_progress',
                'execution_id': execution_id,
                'chain_id': chain.id,
                **progress_data
            })

        # Execute chain
        try:
            results = await self.orchestrator.execute_chain(
                chain.id,
                initial_context=chain_config.get('context', {}),
                progress_callback=progress_callback
            )

            # Send completion
            await self.send_personal_message({
                'type': 'chain_complete',
                'execution_id': execution_id,
                'results': [
                    {
                        'step_id': r.step_id,
                        'status': r.status,
                        'tool': r.tool,
                        'duration': r.duration,
                        'return_code': r.return_code
                    }
                    for r in results
                ]
            }, websocket)

        except Exception as e:
            logger.error(f"Chain execution error: {e}")
            await self.send_personal_message({
                'type': 'chain_error',
                'execution_id': execution_id,
                'error': str(e)
            }, websocket)

    async def kill_execution(self, data: dict):
        """Kill a running execution"""
        execution_id = data.get('execution_id')
        await self.executor.kill(execution_id)
        logger.info(f"Killed execution: {execution_id}")

    # ========== Fractal Visualization Methods ==========

    async def subscribe_to_execution(self, websocket: WebSocket, execution_id: str):
        """Subscribe a client to fractal execution updates"""
        async with self._lock:
            if execution_id not in self.execution_subscriptions:
                self.execution_subscriptions[execution_id] = set()
            self.execution_subscriptions[execution_id].add(websocket)

        logger.info(f"Client subscribed to execution {execution_id}")

        await self.send_personal_message({
            'type': 'subscribed',
            'execution_id': execution_id,
            'timestamp': datetime.utcnow().isoformat()
        }, websocket)

    async def unsubscribe_from_execution(self, websocket: WebSocket, execution_id: str):
        """Unsubscribe a client from fractal execution updates"""
        async with self._lock:
            if execution_id in self.execution_subscriptions:
                self.execution_subscriptions[execution_id].discard(websocket)

        logger.info(f"Client unsubscribed from execution {execution_id}")

        await self.send_personal_message({
            'type': 'unsubscribed',
            'execution_id': execution_id,
            'timestamp': datetime.utcnow().isoformat()
        }, websocket)

    async def broadcast_to_execution(self, execution_id: str, message: Dict[str, Any]):
        """Broadcast message to all subscribers of a specific execution"""
        if execution_id not in self.execution_subscriptions:
            return

        dead_connections = set()
        subscribers = list(self.execution_subscriptions[execution_id])

        for connection in subscribers:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to execution subscriber: {e}")
                dead_connections.add(connection)

        # Clean up dead connections
        async with self._lock:
            self.execution_subscriptions[execution_id] -= dead_connections
            self.active_connections -= dead_connections

    async def send_node_update(self, execution_id: str, node_id: str, updates: Dict[str, Any]):
        """Send fractal node status update"""
        message = {
            'type': 'node_update',
            'execution_id': execution_id,
            'node_id': node_id,
            'updates': updates,
            'timestamp': datetime.utcnow().isoformat()
        }

        await self.broadcast_to_execution(execution_id, message)

    async def send_tree_update(self, execution_id: str, tree: Dict[str, Any]):
        """Send full fractal tree update"""
        message = {
            'type': 'tree_update',
            'execution_id': execution_id,
            'tree': tree,
            'timestamp': datetime.utcnow().isoformat()
        }

        await self.broadcast_to_execution(execution_id, message)

    async def send_metrics_update(self, metrics: Dict[str, Any]):
        """Broadcast system metrics to all clients"""
        message = {
            'type': 'metrics_update',
            'metrics': metrics,
            'timestamp': datetime.utcnow().isoformat()
        }

        await self.broadcast(message)

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            'total_connections': len(self.active_connections),
            'execution_subscriptions': {
                exec_id: len(subscribers)
                for exec_id, subscribers in self.execution_subscriptions.items()
            }
        }


# Global connection manager instance
manager = ConnectionManager()


# ========== Utility Functions for Fractal Orchestrator Integration ==========


async def notify_node_status_change(
    execution_id: str, node_id: str, status: str, result: Any = None
):
    """
    Notify subscribers of a node status change
    Called by fractal orchestrator when node status changes
    """
    updates = {'status': status}
    if result is not None:
        updates['result'] = result

    await manager.send_node_update(execution_id, node_id, updates)


async def notify_tree_update(execution_id: str, tree: Dict[str, Any]):
    """
    Notify subscribers of full tree update
    Called when tree structure changes significantly
    """
    await manager.send_tree_update(execution_id, tree)


async def broadcast_metrics(metrics: Dict[str, Any]):
    """
    Broadcast system metrics to all clients
    """
    await manager.send_metrics_update(metrics)
