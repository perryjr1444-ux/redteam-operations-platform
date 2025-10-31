"""
REST API Endpoints
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Optional
from pydantic import BaseModel
import psutil
from datetime import datetime

from app.tools import get_registry
from app.websocket import manager
from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api")


# Pydantic Models

class ToolExecuteRequest(BaseModel):
    tool: str
    args: dict = {}


class ChainExecuteRequest(BaseModel):
    chain_id: str
    steps: List[dict]
    context: dict = {}


# WebSocket Endpoint

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time tool execution streaming"""
    await manager.connect(websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            # Handle message
            await manager.handle_message(websocket, data)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# REST Endpoints

@router.get("/tools")
async def list_tools():
    """List all available tools"""
    registry = get_registry()
    tools = registry.list_all()

    return [
        {
            'name': tool.name,
            'command': tool.command,
            'category': tool.category,
            'description': tool.description,
            'requires_root': tool.requires_root,
            'timeout': tool.timeout,
            'arguments': [
                {
                    'name': arg.name,
                    'type': arg.type,
                    'required': arg.required,
                    'default': arg.default,
                    'description': arg.description
                }
                for arg in tool.arguments
            ]
        }
        for tool in tools
    ]


@router.get("/tools/{tool_name}")
async def get_tool(tool_name: str):
    """Get details for a specific tool"""
    registry = get_registry()
    tool = registry.get(tool_name)

    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    return {
        'name': tool.name,
        'command': tool.command,
        'category': tool.category,
        'description': tool.description,
        'requires_root': tool.requires_root,
        'timeout': tool.timeout,
        'example': tool.example,
        'arguments': [
            {
                'name': arg.name,
                'type': arg.type,
                'required': arg.required,
                'default': arg.default,
                'description': arg.description,
                'choices': arg.choices
            }
            for arg in tool.arguments
        ]
    }


@router.get("/metrics")
async def get_metrics():
    """Get system and application metrics"""
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # Application metrics (mock for now - should be from database)
    return {
        'activeExercises': len(manager.executor.running_processes),
        'systemHealth': min(100, 100 - cpu_percent),
        'runningTools': len(manager.executor.running_processes),
        'completedChains': 0,  # TODO: Get from database
        'successRate': 85,  # TODO: Calculate from results
        'system': {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_gb': memory.used / (1024 ** 3),
            'memory_total_gb': memory.total / (1024 ** 3),
            'disk_percent': disk.percent,
            'disk_free_gb': disk.free / (1024 ** 3)
        }
    }


@router.get("/results")
async def get_results(limit: int = 50):
    """Get recent execution results"""
    # TODO: Get from database
    # For now, return demo data
    return [
        {
            'id': f'exec_{i}',
            'tool': 'nmap' if i % 2 == 0 else 'sqlmap',
            'status': 'completed' if i % 3 != 0 else 'failed',
            'timestamp': datetime.utcnow().isoformat(),
            'duration': 10.5 + i,
            'return_code': 0 if i % 3 != 0 else 1,
            'output': [
                {'type': 'stdout', 'data': f'Line {j}'}
                for j in range(5)
            ],
            'parsed_data': {
                'summary': f'Result {i}',
                'findings': ['Finding 1', 'Finding 2']
            }
        }
        for i in range(limit)
    ]


@router.get("/topology")
async def get_topology():
    """Get network topology data"""
    # TODO: Build from actual network scans
    # For now, return demo data
    return {
        'nodes': [
            {'id': 'c2', 'type': 'attacker', 'label': 'Red Team C2'},
            {'id': 'web1', 'type': 'target', 'label': 'Web Server', 'ip': '192.168.1.10', 'status': 'compromised'},
            {'id': 'db1', 'type': 'target', 'label': 'Database', 'ip': '192.168.1.20', 'status': 'scanning'},
            {'id': 'fs1', 'type': 'target', 'label': 'File Server', 'ip': '192.168.1.30', 'status': 'unknown'}
        ],
        'links': [
            {'source': 'c2', 'target': 'web1', 'type': 'exploit'},
            {'source': 'c2', 'target': 'db1', 'type': 'scan'},
            {'source': 'web1', 'target': 'db1', 'type': 'connection'}
        ]
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'connections': len(manager.active_connections),
        'running_tools': len(manager.executor.running_processes)
    }
