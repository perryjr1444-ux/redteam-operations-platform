"""
Enhanced UI Routes
Serves enhanced templates with Alpine.js reactive components
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..config import settings
from ..theme import get_theme_context

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))


@router.get("/enhanced", response_class=HTMLResponse)
async def enhanced_dashboard(request: Request):
    """Enhanced dashboard with real-time reactive components"""
    context = {"request": request, "page": "dashboard"}
    context.update(get_theme_context(request))
    return templates.TemplateResponse("dashboard_enhanced.html", context)


@router.get("/ai/dashboard", response_class=HTMLResponse)
async def ai_agents_dashboard(request: Request):
    """AI Agents monitoring dashboard"""
    context = {"request": request, "page": "ai_dashboard", "title": "AI Agents Dashboard"}
    context.update(get_theme_context(request))
    return templates.TemplateResponse("ai_dashboard.html", context)


@router.get("/execution/monitor", response_class=HTMLResponse)
async def execution_monitor(request: Request):
    """Fractal execution monitoring dashboard"""
    context = {"request": request, "page": "execution", "title": "Execution Monitor Dashboard"}
    context.update(get_theme_context(request))
    return templates.TemplateResponse("execution_dashboard.html", context)


@router.get("/chains/builder", response_class=HTMLResponse)
async def chain_builder(request: Request):
    """Interactive attack chain builder"""
    context = {"request": request, "page": "chain_builder", "title": "Attack Chain Builder"}
    context.update(get_theme_context(request))
    return templates.TemplateResponse("chain_builder.html", context)


@router.get("/execution/visualizer", response_class=HTMLResponse)
async def execution_visualizer(request: Request):
    """Fractal execution tree visualizer with D3.js"""
    context = {"request": request, "page": "visualizer", "title": "Execution Visualizer"}
    context.update(get_theme_context(request))
    return templates.TemplateResponse("visualizer.html", context)


@router.get("/dashboard/agents", response_class=HTMLResponse)
async def dashboard_ai_agents(request: Request):
    """AI Agents monitoring dashboard"""
    context = {"request": request, "page": "dashboard_agents", "title": "AI Agents Dashboard"}
    context.update(get_theme_context(request))
    return templates.TemplateResponse("dashboard_ai_agents.html", context)


@router.get("/dashboard/execution", response_class=HTMLResponse)
async def dashboard_execution(request: Request):
    """Execution metrics dashboard"""
    context = {"request": request, "page": "dashboard_execution", "title": "Execution Metrics Dashboard"}
    context.update(get_theme_context(request))
    return templates.TemplateResponse("dashboard_execution.html", context)


@router.get("/dashboard/analytics", response_class=HTMLResponse)
async def dashboard_analytics(request: Request):
    """Security analytics dashboard"""
    context = {"request": request, "page": "dashboard_analytics", "title": "Security Analytics Dashboard"}
    context.update(get_theme_context(request))
    return templates.TemplateResponse("dashboard_analytics.html", context)
