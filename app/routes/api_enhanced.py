"""
Enhanced API Routes for Reactive UI
Provides real-time data endpoints for Alpine.js components

Endpoints:
- /api/metrics/live - Live system metrics
- /api/ai/agents/status - AI agent health status
- /api/execution/active - Active fractal executions
- /api/execution/tree/{id} - Execution tree data
- /api/tools - Available tools registry
- /api/chains - Attack chains (GET/POST)
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import json
from sqlalchemy.orm import Session

from ..ai.agent_manager import AgentManager
from ..fractal_orchestrator import FractalOrchestrator
from ..container_pool import ContainerPool
from ..tools import get_registry, AttackChainOrchestrator, ToolExecutor
from ..tools.chain import ChainDefinition, ChainStep, StepResult, StepStatus
from ..chains.templates import get_all_templates
from ..database import get_db
from ..websocket_chain_monitor import chain_monitor
from .. import crud, schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["api"])

# Global instances (singleton pattern for app lifecycle)
_agent_manager: Optional[AgentManager] = None
_fractal_orchestrator: Optional[FractalOrchestrator] = None
_container_pool: Optional[ContainerPool] = None
_attack_chain_orchestrator: Optional[AttackChainOrchestrator] = None


def get_agent_manager() -> AgentManager:
    """Dependency: Get AgentManager singleton instance"""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager(
            langgraph_url=None,  # Would come from config
            enable_agents=False,  # Disabled by default (enable in config)
            enable_fractal=True
        )
    return _agent_manager


def get_fractal_orchestrator() -> FractalOrchestrator:
    """Dependency: Get FractalOrchestrator singleton instance"""
    global _fractal_orchestrator
    if _fractal_orchestrator is None:
        _fractal_orchestrator = FractalOrchestrator()
    return _fractal_orchestrator


def get_container_pool() -> ContainerPool:
    """Dependency: Get ContainerPool singleton instance"""
    global _container_pool
    if _container_pool is None:
        _container_pool = ContainerPool(
            image="localhost/kali-redteam:latest",
            min_size=3,
            max_size=20,
            prewarm_count=5
        )
    return _container_pool


def get_attack_chain_orchestrator() -> AttackChainOrchestrator:
    """Dependency: Get AttackChainOrchestrator singleton instance"""
    global _attack_chain_orchestrator
    if _attack_chain_orchestrator is None:
        executor = ToolExecutor()
        registry = get_registry()
        _attack_chain_orchestrator = AttackChainOrchestrator(executor, registry)
    return _attack_chain_orchestrator


async def initialize_services():
    """Initialize enhanced services (called during app lifespan startup)"""
    logger.info("Initializing enhanced services...")
    # Services initialize lazily on first use
    # Could pre-initialize here if needed:
    # await get_agent_manager().initialize()
    # await get_container_pool().initialize()
    logger.info("Enhanced services ready (lazy initialization)")


async def shutdown_services():
    """Shutdown enhanced services (called during app lifespan shutdown)"""
    logger.info("Shutting down enhanced services...")

    global _agent_manager, _container_pool

    if _agent_manager:
        await _agent_manager.shutdown()
        logger.info("Agent manager shut down")

    # Container pool shutdown would go here
    # if _container_pool:
    #     await _container_pool.shutdown()

    logger.info("Enhanced services shut down complete")


@router.get("/metrics/live")
async def get_live_metrics(
    agent_mgr: AgentManager = Depends(get_agent_manager),
    pool: ContainerPool = Depends(get_container_pool)
) -> Dict[str, Any]:
    """
    Get live system metrics for dashboard

    Returns:
        {
            "active_exercises": int,
            "system_health": int (0-100),
            "running_containers": int,
            "uptime": str,
            "timestamp": str
        }
    """
    try:
        # Get statistics from various sources
        stats = agent_mgr.get_statistics() if agent_mgr else {}
        pool_stats = pool.get_pool_stats() if pool else {}

        # Calculate uptime
        uptime_seconds = stats.get('uptime_seconds', 0)
        uptime_hours = int(uptime_seconds / 3600)
        uptime_days = int(uptime_hours / 24)

        if uptime_days > 0:
            uptime_str = f"{uptime_days}d"
        else:
            uptime_str = f"{uptime_hours}h"

        # Calculate system health (weighted average)
        agent_health = stats.get('health_status', {}).get('agents', {})
        healthy_agents = sum(1 for a in agent_health.values() if a.get('is_healthy', False))
        total_agents = len(agent_health)
        agent_health_pct = (healthy_agents / total_agents * 100) if total_agents > 0 else 100

        container_health = pool_stats.get('pool_utilization', 0)
        container_health_pct = min(100, (1 - container_health) * 100)  # Lower utilization = healthier

        system_health = int((agent_health_pct * 0.6 + container_health_pct * 0.4))

        return {
            "active_exercises": pool_stats.get('total_acquired', 0),
            "system_health": system_health,
            "running_containers": pool_stats.get('available_count', 0) + pool_stats.get('in_use_count', 0),
            "uptime": uptime_str,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error fetching live metrics: {e}")
        return {
            "active_exercises": 0,
            "system_health": 0,
            "running_containers": 0,
            "uptime": "0h",
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/ai/agents/status")
async def get_agents_status(
    agent_mgr: AgentManager = Depends(get_agent_manager)
) -> Dict[str, Any]:
    """
    Get AI agent health status

    Returns:
        {
            "enabled": bool,
            "agents": {
                "agent_type": {
                    "is_healthy": bool,
                    "last_check": str,
                    "error_count": int,
                    "avg_response_time": float,
                    "uptime_percentage": float
                },
                ...
            }
        }
    """
    try:
        if agent_mgr is None:
            return {"enabled": False, "agents": {}}

        health_status = agent_mgr.get_health_status()
        return health_status

    except Exception as e:
        logger.error(f"Error fetching agent status: {e}")
        return {"enabled": False, "agents": {}}


@router.get("/execution/active")
async def get_active_executions(
    orchestrator: FractalOrchestrator = Depends(get_fractal_orchestrator)
) -> Dict[str, Any]:
    """
    Get active fractal executions

    Returns:
        {
            "executions": [
                {
                    "id": str,
                    "type": str,
                    "status": str,
                    "progress": int,
                    "duration": int
                },
                ...
            ],
            "completed_today": int,
            "avg_duration": float
        }
    """
    try:
        if orchestrator is None:
            return {"executions": [], "completed_today": 0, "avg_duration": 0}

        # Get active executions from orchestrator
        active_nodes = []
        for node_id, node in orchestrator.nodes.items():
            if node.status in ["running", "pending"]:
                # Calculate duration if start_time exists
                duration = 0
                if node.start_time:
                    duration = (datetime.utcnow() - node.start_time).total_seconds()

                # Calculate progress based on status
                progress = 0
                if node.status.value == "running":
                    progress = 50  # Mock progress
                elif node.status.value == "completed":
                    progress = 100

                active_nodes.append({
                    "id": node.id,
                    "type": node.type,
                    "status": node.status.value,
                    "progress": progress,
                    "duration": int(duration),
                    "level": node.level.value,
                    "nodeCount": len(orchestrator.get_children(node_id))
                })

        return {
            "executions": active_nodes,
            "completed_today": 15,  # Mock data - would query from database
            "avg_duration": 145.5  # Mock data - would calculate from history
        }

    except Exception as e:
        logger.error(f"Error fetching active executions: {e}")
        return {"executions": [], "completed_today": 0, "avg_duration": 0}


@router.get("/execution/tree/{root_id}")
async def get_execution_tree(
    root_id: str,
    orchestrator: FractalOrchestrator = Depends(get_fractal_orchestrator)
) -> Dict[str, Any]:
    """
    Get execution tree structure for visualization

    Args:
        root_id: Root node ID

    Returns:
        {
            "id": str,
            "type": str,
            "status": str,
            "level": str,
            "children": [...]
        }
    """
    try:
        if orchestrator is None:
            raise HTTPException(status_code=503, detail="Orchestrator not available")

        node = orchestrator.get_node(root_id)
        if node is None:
            raise HTTPException(status_code=404, detail=f"Node {root_id} not found")

        def build_tree(node_id: str) -> Dict[str, Any]:
            """Recursively build tree structure"""
            node = orchestrator.get_node(node_id)
            if node is None:
                return {}

            children = [
                build_tree(child_id)
                for child_id in orchestrator.nodes.keys()
                if orchestrator.nodes[child_id].parent_id == node_id
            ]

            return {
                "id": node.id,
                "type": node.type,
                "status": node.status.value,
                "level": node.level.value,
                "result": node.result if node.result else None,
                "children": children
            }

        tree = build_tree(root_id)
        return tree

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching execution tree: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def get_tools() -> Dict[str, Any]:
    """
    Get available tools registry

    Returns:
        {
            "tools": [
                {
                    "name": str,
                    "category": str,
                    "description": str,
                    "requires_root": bool
                },
                ...
            ]
        }
    """
    try:
        registry = get_registry()
        tool_list = [
            {
                "name": name,
                "category": tool.category.value,
                "description": tool.description,
                "requires_root": tool.requires_root,
                "timeout": tool.timeout
            }
            for name, tool in registry.tools.items()
        ]

        return {"tools": tool_list}

    except Exception as e:
        logger.error(f"Error fetching tools: {e}")
        return {"tools": []}


@router.get("/chains")
async def get_chains(
    include_templates: bool = True,
    include_inactive: bool = False,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get available attack chains (both templates and custom chains)

    Args:
        include_templates: Include built-in templates (default: True)
        include_inactive: Include inactive/deleted chains (default: False)
        db: Database session

    Returns:
        {
            "templates": [...],  # Built-in templates
            "custom_chains": [...],  # User-created chains from database
            "total": int
        }
    """
    try:
        result = {
            "templates": [],
            "custom_chains": [],
            "total": 0
        }

        # Get built-in templates
        if include_templates:
            templates = get_all_templates()
            result["templates"] = [
                {
                    "id": template.id,
                    "name": template.name,
                    "category": template.category,
                    "risk_level": template.risk_level,
                    "estimated_duration": template.estimated_duration,
                    "step_count": len(template.steps),
                    "is_template": True
                }
                for template in templates
            ]

        # Get custom chains from database
        db_chains = crud.get_attack_chains(db, include_inactive=include_inactive)
        result["custom_chains"] = [
            {
                "id": chain.chain_id,
                "name": chain.name,
                "description": chain.description,
                "category": chain.category,
                "risk_level": chain.risk_level,
                "step_count": len(json.loads(chain.steps)) if chain.steps else 0,
                "is_template": chain.is_template,
                "is_active": chain.is_active,
                "created_by": chain.created_by,
                "created_at": chain.created_at.isoformat() if chain.created_at else None,
                "updated_at": chain.updated_at.isoformat() if chain.updated_at else None
            }
            for chain in db_chains
        ]

        result["total"] = len(result["templates"]) + len(result["custom_chains"])

        return result

    except Exception as e:
        logger.error(f"Error fetching chains: {e}", exc_info=True)
        return {"templates": [], "custom_chains": [], "total": 0}


@router.post("/chains", response_model=schemas.AttackChainResponse)
async def create_chain(
    chain: schemas.AttackChainCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new attack chain

    Args:
        chain: AttackChainCreate schema with:
            - name: Chain name
            - description: Optional description
            - category: Optional category
            - risk_level: Risk level (low/medium/high/critical)
            - steps: List of chain steps
            - metadata: Optional metadata dict
            - chain_id: Optional custom chain_id (auto-generated if not provided)
            - is_template: Mark as template (default: False)

    Returns:
        AttackChainResponse with created chain details
    """
    try:
        # Convert Pydantic model to dict for CRUD
        chain_dict = chain.model_dump()

        # Add creator info (would come from auth in production)
        chain_dict["created_by"] = "api_user"  # TODO: Get from auth context

        # Create in database
        db_chain = crud.create_attack_chain(db, chain_dict)

        # Parse JSON fields back to dicts for response
        response_data = {
            "id": db_chain.id,
            "chain_id": db_chain.chain_id,
            "name": db_chain.name,
            "description": db_chain.description,
            "category": db_chain.category,
            "risk_level": db_chain.risk_level,
            "steps": json.loads(db_chain.steps) if db_chain.steps else [],
            "metadata": json.loads(db_chain.chain_metadata) if db_chain.chain_metadata else None,
            "created_by": db_chain.created_by,
            "created_at": db_chain.created_at,
            "updated_at": db_chain.updated_at,
            "is_template": db_chain.is_template,
            "is_active": db_chain.is_active
        }

        logger.info(f"Created attack chain: {db_chain.chain_id} (name: {db_chain.name})")

        return schemas.AttackChainResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating chain: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chains/executions")
async def get_chain_executions(
    chain_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get chain execution history

    Args:
        chain_id: Optional filter by chain_id
        skip: Pagination offset
        limit: Pagination limit
        db: Database session

    Returns:
        List of chain executions
    """
    try:
        db_executions = crud.get_chain_executions(db, chain_id=chain_id, skip=skip, limit=limit)

        executions = [
            {
                "id": ex.id,
                "execution_id": ex.execution_id,
                "chain_id": ex.chain_id,
                "chain_name": ex.chain_name,
                "status": ex.status,
                "total_steps": ex.total_steps,
                "completed_steps": ex.completed_steps,
                "failed_steps": ex.failed_steps,
                "skipped_steps": ex.skipped_steps,
                "start_time": ex.start_time.isoformat() if ex.start_time else None,
                "end_time": ex.end_time.isoformat() if ex.end_time else None,
                "duration": ex.duration,
                "executed_by": ex.executed_by,
                "error_message": ex.error_message,
                "created_at": ex.created_at.isoformat() if ex.created_at else None
            }
            for ex in db_executions
        ]

        return {
            "success": True,
            "executions": executions,
            "total": len(executions)
        }

    except Exception as e:
        logger.error(f"Error fetching executions: {e}", exc_info=True)
        return {"success": False, "executions": [], "total": 0}


@router.get("/chains/executions/{execution_id}", response_model=schemas.ChainExecutionResponse)
async def get_chain_execution(execution_id: str, db: Session = Depends(get_db)):
    """
    Get specific chain execution details

    Args:
        execution_id: Execution identifier
        db: Database session

    Returns:
        ChainExecutionResponse with execution details
    """
    try:
        # Check if execution exists BEFORE any operations
        db_execution = crud.get_chain_execution_by_id(db, execution_id)
        if not db_execution:
            raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

        # Parse results back to list for response
        response_data = {
            "id": db_execution.id,
            "execution_id": db_execution.execution_id,
            "chain_id": db_execution.chain_id,
            "chain_name": db_execution.chain_name,
            "status": db_execution.status,
            "total_steps": db_execution.total_steps,
            "completed_steps": db_execution.completed_steps,
            "failed_steps": db_execution.failed_steps,
            "skipped_steps": db_execution.skipped_steps,
            "results": json.loads(db_execution.results) if db_execution.results else [],
            "start_time": db_execution.start_time,
            "end_time": db_execution.end_time,
            "duration": db_execution.duration,
            "executed_by": db_execution.executed_by,
            "error_message": db_execution.error_message,
            "created_at": db_execution.created_at
        }

        return schemas.ChainExecutionResponse(**response_data)

    except HTTPException:
        # Re-raise HTTPException (including 404) without modification
        raise
    except Exception as e:
        # Log and convert unexpected errors to 500
        logger.error(f"Unexpected error fetching execution {execution_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chains/{chain_id}", response_model=schemas.AttackChainResponse)
async def get_chain(chain_id: str, db: Session = Depends(get_db)):
    """
    Get specific attack chain by chain_id

    Args:
        chain_id: Chain identifier
        db: Database session

    Returns:
        AttackChainResponse with chain details
    """
    try:
        # Check if chain exists BEFORE any operations
        db_chain = crud.get_attack_chain_by_chain_id(db, chain_id)
        if not db_chain:
            raise HTTPException(status_code=404, detail=f"Chain {chain_id} not found")

        # Parse JSON fields back to dicts for response
        response_data = {
            "id": db_chain.id,
            "chain_id": db_chain.chain_id,
            "name": db_chain.name,
            "description": db_chain.description,
            "category": db_chain.category,
            "risk_level": db_chain.risk_level,
            "steps": json.loads(db_chain.steps) if db_chain.steps else [],
            "metadata": json.loads(db_chain.chain_metadata) if db_chain.chain_metadata else None,
            "created_by": db_chain.created_by,
            "created_at": db_chain.created_at,
            "updated_at": db_chain.updated_at,
            "is_template": db_chain.is_template,
            "is_active": db_chain.is_active
        }

        return schemas.AttackChainResponse(**response_data)

    except HTTPException:
        # Re-raise HTTPException (including 404) without modification
        raise
    except Exception as e:
        # Log and convert unexpected errors to 500
        logger.error(f"Unexpected error fetching chain {chain_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/chains/{chain_id}", response_model=schemas.AttackChainResponse)
async def update_chain(
    chain_id: str,
    chain_update: schemas.AttackChainUpdate,
    db: Session = Depends(get_db)
):
    """
    Update attack chain

    Args:
        chain_id: Chain identifier
        chain_update: AttackChainUpdate schema with fields to update
        db: Database session

    Returns:
        AttackChainResponse with updated chain details
    """
    try:
        # Check if chain exists BEFORE any operations
        existing_chain = crud.get_attack_chain_by_chain_id(db, chain_id)
        if not existing_chain:
            raise HTTPException(status_code=404, detail=f"Chain {chain_id} not found")

        # Convert Pydantic model to dict, excluding unset fields
        update_dict = chain_update.model_dump(exclude_unset=True)

        # Update in database
        db_chain = crud.update_attack_chain(db, chain_id, update_dict)

        if not db_chain:
            raise HTTPException(status_code=500, detail="Failed to update chain")

        # Parse JSON fields back to dicts for response
        response_data = {
            "id": db_chain.id,
            "chain_id": db_chain.chain_id,
            "name": db_chain.name,
            "description": db_chain.description,
            "category": db_chain.category,
            "risk_level": db_chain.risk_level,
            "steps": json.loads(db_chain.steps) if db_chain.steps else [],
            "metadata": json.loads(db_chain.chain_metadata) if db_chain.chain_metadata else None,
            "created_by": db_chain.created_by,
            "created_at": db_chain.created_at,
            "updated_at": db_chain.updated_at,
            "is_template": db_chain.is_template,
            "is_active": db_chain.is_active
        }

        logger.info(f"Updated attack chain: {chain_id}")

        return schemas.AttackChainResponse(**response_data)

    except HTTPException:
        # Re-raise HTTPException (including 404) without modification
        raise
    except Exception as e:
        # Log and convert unexpected errors to 500
        logger.error(f"Unexpected error updating chain {chain_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chains/{chain_id}")
async def delete_chain(chain_id: str, db: Session = Depends(get_db)):
    """
    Delete attack chain (soft delete - sets is_active=False)

    Args:
        chain_id: Chain identifier
        db: Database session

    Returns:
        Success message
    """
    try:
        # Check if chain exists BEFORE any operations
        existing_chain = crud.get_attack_chain_by_chain_id(db, chain_id)
        if not existing_chain:
            raise HTTPException(status_code=404, detail=f"Chain {chain_id} not found")

        # Soft delete
        success = crud.delete_attack_chain(db, chain_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete chain")

        logger.info(f"Deleted attack chain: {chain_id}")

        return {
            "success": True,
            "chain_id": chain_id,
            "message": f"Chain {chain_id} deleted successfully"
        }

    except HTTPException:
        # Re-raise HTTPException (including 404) without modification
        raise
    except Exception as e:
        # Log and convert unexpected errors to 500
        logger.error(f"Unexpected error deleting chain {chain_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def convert_db_chain_to_definition(db_chain, steps: List[Dict[str, Any]]) -> ChainDefinition:
    """
    Convert database chain model to ChainDefinition format

    Args:
        db_chain: Database chain model
        steps: Parsed steps list from JSON

    Returns:
        ChainDefinition object
    """
    chain_steps = []
    for step_data in steps:
        chain_step = ChainStep(
            id=step_data.get("id", f"step_{len(chain_steps)}"),
            tool=step_data.get("tool", ""),
            args=step_data.get("args", {}),
            depends_on=step_data.get("depends_on", []),
            data_mapping=step_data.get("data_mapping", {}),
            condition=step_data.get("condition"),
            parallel=step_data.get("parallel", False),
            on_error=step_data.get("on_error", "stop")
        )
        chain_steps.append(chain_step)

    metadata = json.loads(db_chain.chain_metadata) if db_chain.chain_metadata else {}

    return ChainDefinition(
        id=db_chain.chain_id,
        name=db_chain.name,
        description=db_chain.description or "",
        steps=chain_steps,
        metadata=metadata
    )


def convert_step_results_to_json(step_results: List[StepResult]) -> List[Dict[str, Any]]:
    """
    Convert StepResult objects to JSON-serializable format

    Args:
        step_results: List of StepResult objects

    Returns:
        List of dictionaries
    """
    results = []
    for result in step_results:
        results.append({
            "step_id": result.step_id,
            "status": result.status.value if isinstance(result.status, StepStatus) else result.status,
            "tool": result.tool,
            "output": result.output,
            "parsed_data": result.parsed_data,
            "return_code": result.return_code,
            "duration": result.duration,
            "error": result.error,
            "start_time": result.start_time.isoformat() if result.start_time else None,
            "end_time": result.end_time.isoformat() if result.end_time else None
        })
    return results


async def execute_chain_background(
    execution_id: str,
    chain_definition: ChainDefinition,
    initial_context: Dict[str, Any],
    orchestrator: AttackChainOrchestrator,
    db: Session
):
    """
    Background task to execute chain and update database with WebSocket notifications

    Args:
        execution_id: Execution record ID
        chain_definition: ChainDefinition to execute
        initial_context: Initial execution context
        orchestrator: AttackChainOrchestrator instance
        db: Database session
    """
    start_time = datetime.utcnow()

    try:
        # Update execution status to running
        crud.update_chain_execution(db, execution_id, {
            "status": "running",
            "start_time": start_time
        })

        # Send initial execution update via WebSocket
        await chain_monitor.send_execution_update(execution_id, db)

        # Register and execute chain
        orchestrator.register_chain(chain_definition)

        # Execute chain with progress tracking
        step_results = []
        for step_index, step in enumerate(chain_definition.steps):
            # Send step start notification
            await chain_monitor.send_step_start(
                execution_id=execution_id,
                step_index=step_index,
                step_name=step.id,
                tool=step.tool,
                start_time=datetime.utcnow()
            )

            try:
                # Execute single step (would call actual orchestrator method)
                # For now, we'll execute the full chain and track results
                if step_index == 0:
                    step_results = await orchestrator.execute_chain(
                        chain_definition.id,
                        initial_context=initial_context
                    )

                # Get result for this step
                if step_index < len(step_results):
                    step_result = step_results[step_index]

                    # Send step completion or failure
                    if step_result.status == StepStatus.COMPLETED:
                        await chain_monitor.send_step_complete(
                            execution_id=execution_id,
                            step_index=step_index,
                            end_time=step_result.end_time or datetime.utcnow(),
                            duration=step_result.duration or 0,
                            output=step_result.output.split('\n') if step_result.output else []
                        )
                    elif step_result.status == StepStatus.FAILED:
                        await chain_monitor.send_step_failed(
                            execution_id=execution_id,
                            step_index=step_index,
                            end_time=step_result.end_time or datetime.utcnow(),
                            duration=step_result.duration or 0,
                            error=step_result.error or "Step failed",
                            output=step_result.output.split('\n') if step_result.output else []
                        )

                    # Update database with intermediate progress
                    completed_steps = sum(1 for r in step_results[:step_index+1] if r.status == StepStatus.COMPLETED)
                    failed_steps = sum(1 for r in step_results[:step_index+1] if r.status == StepStatus.FAILED)

                    crud.update_chain_execution(db, execution_id, {
                        "completed_steps": completed_steps,
                        "failed_steps": failed_steps
                    })

            except Exception as step_error:
                logger.error(f"Step {step_index} failed: {step_error}")
                await chain_monitor.send_step_failed(
                    execution_id=execution_id,
                    step_index=step_index,
                    end_time=datetime.utcnow(),
                    duration=0,
                    error=str(step_error),
                    output=[]
                )

        # Calculate statistics
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        completed_steps = sum(1 for r in step_results if r.status == StepStatus.COMPLETED)
        failed_steps = sum(1 for r in step_results if r.status == StepStatus.FAILED)
        skipped_steps = sum(1 for r in step_results if r.status == StepStatus.SKIPPED)

        # Determine overall status
        if failed_steps > 0:
            overall_status = "failed"
        elif completed_steps == len(step_results):
            overall_status = "completed"
        else:
            overall_status = "partial"

        # Convert results to JSON-serializable format
        results_json = convert_step_results_to_json(step_results)

        # Update execution record
        crud.update_chain_execution(db, execution_id, {
            "status": overall_status,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "skipped_steps": skipped_steps,
            "results": results_json,
            "end_time": end_time,
            "duration": duration
        })

        # Send completion notification via WebSocket
        if overall_status == "completed":
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
                error=f"{failed_steps} steps failed"
            )

        logger.info(
            f"Chain execution {execution_id} completed: "
            f"{completed_steps}/{len(step_results)} steps successful, "
            f"{failed_steps} failed, {skipped_steps} skipped"
        )

    except Exception as e:
        logger.error(f"Chain execution {execution_id} failed: {e}", exc_info=True)

        # Update execution with error
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        crud.update_chain_execution(db, execution_id, {
            "status": "error",
            "error_message": str(e),
            "end_time": end_time,
            "duration": duration
        })

        # Send error notification via WebSocket
        await chain_monitor.send_execution_failed(
            execution_id=execution_id,
            end_time=end_time,
            duration=duration,
            error=str(e)
        )


@router.post("/chains/{chain_id}/execute", response_model=schemas.ChainExecutionResponse)
async def execute_chain(
    chain_id: str,
    execution_request: schemas.ChainExecutionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    orchestrator: AttackChainOrchestrator = Depends(get_attack_chain_orchestrator)
):
    """
    Execute attack chain

    Args:
        chain_id: Chain identifier to execute
        execution_request: ChainExecutionCreate with optional context
        background_tasks: FastAPI background tasks
        db: Database session
        orchestrator: AttackChainOrchestrator instance

    Returns:
        ChainExecutionResponse with execution details
    """
    try:
        # Check if chain exists BEFORE any operations
        db_chain = crud.get_attack_chain_by_chain_id(db, chain_id)
        if not db_chain:
            raise HTTPException(status_code=404, detail=f"Chain {chain_id} not found")

        if not db_chain.is_active:
            raise HTTPException(status_code=400, detail=f"Chain {chain_id} is inactive")

        # Parse steps
        steps = json.loads(db_chain.steps) if db_chain.steps else []

        if not steps:
            raise HTTPException(status_code=400, detail=f"Chain {chain_id} has no steps")

        # Convert database chain to ChainDefinition
        chain_definition = convert_db_chain_to_definition(db_chain, steps)

        # Create execution record
        execution_data = {
            "chain_id": chain_id,
            "chain_name": db_chain.name,
            "status": "pending",
            "total_steps": len(steps),
            "completed_steps": 0,
            "failed_steps": 0,
            "skipped_steps": 0,
            "results": [],
            "executed_by": "api_user"  # TODO: Get from auth context
        }

        db_execution = crud.create_chain_execution(db, execution_data)

        # Get initial context from request
        initial_context = execution_request.context if hasattr(execution_request, 'context') else {}

        # Schedule background execution
        background_tasks.add_task(
            execute_chain_background,
            db_execution.execution_id,
            chain_definition,
            initial_context,
            orchestrator,
            db
        )

        # Parse results back to list for response
        response_data = {
            "id": db_execution.id,
            "execution_id": db_execution.execution_id,
            "chain_id": db_execution.chain_id,
            "chain_name": db_execution.chain_name,
            "status": db_execution.status,
            "total_steps": db_execution.total_steps,
            "completed_steps": db_execution.completed_steps,
            "failed_steps": db_execution.failed_steps,
            "skipped_steps": db_execution.skipped_steps,
            "results": json.loads(db_execution.results) if db_execution.results else [],
            "start_time": db_execution.start_time,
            "end_time": db_execution.end_time,
            "duration": db_execution.duration,
            "executed_by": db_execution.executed_by,
            "error_message": db_execution.error_message,
            "created_at": db_execution.created_at
        }

        logger.info(
            f"Scheduled chain execution: {db_execution.execution_id} for chain {chain_id} "
            f"with {len(steps)} steps"
        )

        return schemas.ChainExecutionResponse(**response_data)

    except HTTPException:
        # Re-raise HTTPException (including 404) without modification
        raise
    except Exception as e:
        # Log and convert unexpected errors to 500
        logger.error(f"Unexpected error executing chain {chain_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/activity")
async def get_activity_metrics() -> Dict[str, Any]:
    """
    Get comprehensive activity metrics for dashboard

    Returns:
        {
            "completed_operations": int,
            "total_operations": int,
            "operation_status": {
                "success": int,
                "failed": int,
                "pending": int
            },
            "tool_usage": {
                "nmap": int,
                "sqlmap": int,
                "metasploit": int,
                ...
            },
            "recent_activity": [
                {
                    "type": str,
                    "message": str,
                    "details": str,
                    "timestamp": str
                }
            ],
            "timeline": {
                "labels": [str],
                "values": [int]
            }
        }
    """
    try:
        import random

        # In production, this would query database for real data
        # Generate realistic mock data for demonstration

        # Operation statistics
        total_ops = random.randint(50, 150)
        completed_ops = random.randint(int(total_ops * 0.7), int(total_ops * 0.9))
        success_ops = random.randint(int(completed_ops * 0.8), completed_ops)
        failed_ops = completed_ops - success_ops
        pending_ops = total_ops - completed_ops

        # Tool usage statistics
        tools = ['nmap', 'sqlmap', 'metasploit', 'nikto', 'gobuster', 'hydra']
        tool_usage = {tool: random.randint(5, 30) for tool in tools}

        # Recent activity log
        activity_types = [
            ('operation', 'Nmap scan completed', 'Target: 192.168.1.100'),
            ('container', 'Container started', 'Kali Linux instance'),
            ('operation', 'SQLMap injection test initiated', 'Target: example.com/login'),
            ('success', 'Vulnerability discovered', 'SQL injection found'),
            ('operation', 'Metasploit exploit executed', 'Exploit: ms17_010'),
            ('container', 'Container stopped', 'Container ID: abc123'),
            ('operation', 'Port scan completed', '65535 ports scanned'),
            ('success', 'Credentials obtained', 'Username/password discovered'),
            ('operation', 'Directory enumeration started', 'Using gobuster wordlist'),
            ('container', 'Container spawned', 'New Kali instance')
        ]

        now = datetime.utcnow()
        recent_activity = []
        for i, (type_, message, details) in enumerate(random.sample(activity_types, min(10, len(activity_types)))):
            timestamp = now - timedelta(minutes=random.randint(1, 120))
            recent_activity.append({
                'type': type_,
                'message': message,
                'details': details,
                'timestamp': timestamp.isoformat()
            })

        # Sort by timestamp descending
        recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)

        # Timeline data (last 7 days)
        timeline_labels = []
        timeline_values = []
        for i in range(6, -1, -1):
            date = datetime.utcnow() - timedelta(days=i)
            timeline_labels.append(date.strftime('%a'))
            timeline_values.append(random.randint(5, 25))

        return {
            "completed_operations": completed_ops,
            "total_operations": total_ops,
            "operation_status": {
                "success": success_ops,
                "failed": failed_ops,
                "pending": pending_ops
            },
            "tool_usage": tool_usage,
            "recent_activity": recent_activity,
            "timeline": {
                "labels": timeline_labels,
                "values": timeline_values
            }
        }

    except Exception as e:
        logger.error(f"Error fetching activity metrics: {e}")
        return {
            "completed_operations": 0,
            "total_operations": 0,
            "operation_status": {"success": 0, "failed": 0, "pending": 0},
            "tool_usage": {},
            "recent_activity": [],
            "timeline": {"labels": [], "values": []}
        }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    API health check endpoint

    Returns:
        {
            "status": str,
            "timestamp": str,
            "services": {
                "agents": bool,
                "orchestrator": bool,
                "containers": bool
            }
        }
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "agents": _agent_manager is not None,
            "orchestrator": _fractal_orchestrator is not None,
            "containers": _container_pool is not None
        }
    }


# ==================== Agent Control Endpoints ====================

@router.post("/ai/agents/{agent_type}/start")
async def start_agent(
    agent_type: str,
    agent_mgr: AgentManager = Depends(get_agent_manager)
) -> Dict[str, Any]:
    """
    Start a specific AI agent

    Args:
        agent_type: Type of agent to start (e.g., 'attack_planner', 'vuln_analyzer')

    Returns:
        {
            "success": bool,
            "message": str,
            "agent_type": str
        }
    """
    try:
        logger.info(f"Starting agent: {agent_type}")

        # In production, this would actually start the agent
        # For now, we'll simulate the operation
        return {
            "success": True,
            "message": f"Agent {agent_type} started successfully",
            "agent_type": agent_type,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error starting agent {agent_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/agents/{agent_type}/stop")
async def stop_agent(
    agent_type: str,
    agent_mgr: AgentManager = Depends(get_agent_manager)
) -> Dict[str, Any]:
    """
    Stop a specific AI agent

    Args:
        agent_type: Type of agent to stop

    Returns:
        {
            "success": bool,
            "message": str,
            "agent_type": str
        }
    """
    try:
        logger.info(f"Stopping agent: {agent_type}")

        # In production, this would actually stop the agent
        return {
            "success": True,
            "message": f"Agent {agent_type} stopped successfully",
            "agent_type": agent_type,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error stopping agent {agent_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/agents/{agent_type}/restart")
async def restart_agent(
    agent_type: str,
    agent_mgr: AgentManager = Depends(get_agent_manager)
) -> Dict[str, Any]:
    """
    Restart a specific AI agent

    Args:
        agent_type: Type of agent to restart

    Returns:
        {
            "success": bool,
            "message": str,
            "agent_type": str
        }
    """
    try:
        logger.info(f"Restarting agent: {agent_type}")

        # In production, this would stop and start the agent
        return {
            "success": True,
            "message": f"Agent {agent_type} restarted successfully",
            "agent_type": agent_type,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error restarting agent {agent_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/agents/{agent_type}/query")
async def query_agent(
    agent_type: str,
    query_data: Dict[str, Any],
    agent_mgr: AgentManager = Depends(get_agent_manager)
) -> Dict[str, Any]:
    """
    Send a query to a specific AI agent

    Args:
        agent_type: Type of agent to query
        query_data: {
            "query": str,
            "query_id": int (optional)
        }

    Returns:
        {
            "success": bool,
            "response": str,
            "agent_type": str,
            "query_id": int,
            "processing_time": float
        }
    """
    try:
        query = query_data.get('query', '')
        query_id = query_data.get('query_id', None)

        if not query:
            raise HTTPException(status_code=400, detail="Query is required")

        logger.info(f"Agent {agent_type} received query: {query[:100]}...")

        # Simulate processing time
        import time
        start_time = time.time()

        # In production, this would send the query to the actual agent
        # For demonstration, we'll return a mock response
        mock_responses = {
            'attack_planner': f"Attack plan analysis: Based on your query '{query}', I recommend a multi-stage reconnaissance approach followed by targeted exploitation.",
            'vuln_analyzer': f"Vulnerability assessment: Analyzing query '{query}'. Identified potential attack vectors in web application layer.",
            'exploit_advisor': f"Exploit recommendation: For '{query}', consider using targeted SQL injection followed by privilege escalation.",
            'chain_optimizer': f"Chain optimization: Analyzing '{query}'. Optimal execution order: reconnaissance -> enumeration -> exploitation.",
            'agent_coordinator': f"Agent coordination: Dispatching query '{query}' to specialized agents for comprehensive analysis."
        }

        response = mock_responses.get(agent_type, f"Agent {agent_type} processed query: {query}")

        processing_time = time.time() - start_time

        return {
            "success": True,
            "response": response,
            "agent_type": agent_type,
            "query_id": query_id,
            "processing_time": round(processing_time * 1000, 2),  # Convert to ms
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying agent {agent_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
