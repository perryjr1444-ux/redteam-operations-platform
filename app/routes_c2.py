"""
New C2 Interface Routes

Routes for the military-grade C2 interface
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .database import get_db
from .config import settings

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def c2_dashboard(request: Request):
    """C2 Dashboard - Main tactical overview"""
    return templates.TemplateResponse(
        "c2_dashboard.html",
        {"request": request, "page": "dashboard"}
    )


@router.get("/chains", response_class=HTMLResponse)
async def c2_chains(request: Request):
    """C2 Attack Chains - Workflow builder"""
    return templates.TemplateResponse(
        "c2_chains.html",
        {"request": request, "page": "chains"}
    )


@router.get("/results", response_class=HTMLResponse)
async def c2_results(request: Request):
    """C2 Results - Execution history and analysis"""
    return templates.TemplateResponse(
        "c2_results.html",
        {"request": request, "page": "results"}
    )


@router.get("/tools", response_class=HTMLResponse)
async def c2_tools(request: Request):
    """C2 Tools - Arsenal catalog"""
    from .tools import get_registry

    registry = get_registry()
    tools = registry.list_all()

    # Group by category
    tools_by_category = {}
    for tool in tools:
        category = tool.category.value
        if category not in tools_by_category:
            tools_by_category[category] = []
        tools_by_category[category].append(tool)

    return templates.TemplateResponse(
        "c2_tools.html",
        {
            "request": request,
            "page": "tools",
            "tools_by_category": tools_by_category
        }
    )


@router.get("/topology", response_class=HTMLResponse)
async def c2_topology(request: Request):
    """C2 Network Topology - Threat map"""
    return templates.TemplateResponse(
        "c2_topology.html",
        {"request": request, "page": "topology"}
    )
