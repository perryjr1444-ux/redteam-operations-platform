"""Red Team Exercise Management Application - Main Entry Point."""

import yaml
import random
import re
import json
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends, Form, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .config import settings, validate_production_config
from .database import SessionLocal, engine, get_db, init_db
from .logger import logger
from .middleware import setup_middleware, limiter
from .podman_service import podman_service
from .websocket_terminal import terminal_streamer
from .websocket_chain_monitor import chain_monitor
from .theme import get_theme_context


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting application")

    # Validate production configuration
    validate_production_config()

    # Ensure directories exist
    settings.DB_DIR.mkdir(exist_ok=True)

    # Initialize database tables
    logger.info("Initializing database tables...")
    init_db()
    logger.info("Database tables initialized")

    # Populate initial data
    if settings.AUTO_POPULATE:
        db = SessionLocal()
        try:
            populate_initial_data(db)
        finally:
            db.close()

    logger.info("Application startup complete")
    yield
    logger.info("Application shutting down")


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Setup middleware
app = setup_middleware(app)

# Include routers
from .api import router as api_router
from .routes_c2 import router as c2_router
from .routes.ui_enhanced import router as ui_enhanced_router
from .routes.api_enhanced import router as api_enhanced_router
from .routes.theme import router as theme_router
from .routes.api_dashboards import router as dashboard_router
from .routes.purple_team_api import router as purple_team_router

app.include_router(api_router)
app.include_router(c2_router)
app.include_router(ui_enhanced_router)
app.include_router(api_enhanced_router)
app.include_router(theme_router)
app.include_router(dashboard_router)
app.include_router(purple_team_router)


# Data population
def populate_initial_data(db: Session):
    """Populate initial templates and exercises with comprehensive seed data."""
    from .seed_data import TEMPLATES, EXERCISES

    # Populate templates
    if not crud.get_templates(db):
        logger.info(f"Populating {len(TEMPLATES)} templates")
        for template in TEMPLATES:
            try:
                crud.create_template(db=db, template=template)
            except Exception as e:
                logger.error(f"Failed to create template {template.get('template_id')}: {e}")
        logger.info(f"Populated {len(TEMPLATES)} templates")
    else:
        logger.info("Templates already exist, skipping population")

    # Populate sample exercises
    if not crud.get_exercises(db):
        logger.info(f"Populating {len(EXERCISES)} sample exercises")
        for exercise in EXERCISES:
            try:
                crud.create_exercise(db=db, exercise=exercise)
            except Exception as e:
                logger.error(f"Failed to create exercise {exercise.get('exercise_id')}: {e}")
        logger.info(f"Populated {len(EXERCISES)} sample exercises")
    else:
        logger.info("Exercises already exist, skipping population")


# Mount static files & templates
app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))


# === API Endpoints ===


@app.get("/api/health", response_model=schemas.HealthCheckResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def health_check(request: Request, db: Session = Depends(get_db)):
    """Health check endpoint for monitoring."""
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        )

    return schemas.HealthCheckResponse(
        status="healthy",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        database=db_status,
        timestamp=datetime.utcnow(),
    )


@app.get("/api/readiness")
async def readiness_probe():
    """Kubernetes readiness probe."""
    return {"status": "ready"}


@app.get("/api/liveness")
async def liveness_probe():
    """Kubernetes liveness probe."""
    return {"status": "alive"}


# === Authentication Endpoints ===


@app.post("/api/auth/register")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def register(request: Request, db: Session = Depends(get_db)):
    """Register a new user."""
    from .auth import UserCreate, create_user, UserResponse

    try:
        data = await request.json()
        user_data = UserCreate(**data)

        # Validate password strength
        if len(user_data.password) < 8:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters long"
            )

        user = create_user(db, user_data)
        logger.info(f"New user registered: {user.username}")

        return JSONResponse(
            status_code=201,
            content={
                "message": "User created successfully",
                "user": UserResponse.model_validate(user).model_dump()
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Registration failed")


@app.post("/api/auth/login")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def login(request: Request, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    from .auth import UserLogin, authenticate_user, create_access_token
    from datetime import timedelta

    try:
        data = await request.json()
        login_data = UserLogin(**data)

        user = authenticate_user(db, login_data.username, login_data.password)

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password"
            )

        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()

        # Create access token
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id}
        )

        logger.info(f"User logged in: {user.username}")

        return JSONResponse(
            content={
                "access_token": access_token,
                "token_type": "bearer",
                "username": user.username,
                "user_id": user.id
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Login failed")


@app.get("/api/auth/me")
async def get_current_user_info(request: Request, db: Session = Depends(get_db)):
    """Get current user information."""
    from .auth import get_current_user, UserResponse

    try:
        user = await get_current_user(request, db)
        return UserResponse.model_validate(user).model_dump()
    except Exception as e:
        logger.error(f"Get user info error: {e}", exc_info=True)
        raise


# === Web UI Routes ===


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    context = {"request": request}
    context.update(get_theme_context(request))
    return templates.TemplateResponse("login.html", context)


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Registration page."""
    context = {"request": request}
    context.update(get_theme_context(request))
    return templates.TemplateResponse("register.html", context)


# Legacy dashboard route - replaced by C2 interface
# @app.get("/", response_class=HTMLResponse)
# @limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
# async def read_root(request: Request):
#     """Dashboard page."""
#     return templates.TemplateResponse(
#         "dashboard.html", {"request": request, "page": "dashboard"}
#     )


@app.get("/health", response_class=HTMLResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def read_health(request: Request):
    """Health monitoring page."""
    context = {"request": request, "page": "health"}
    context.update(get_theme_context(request))
    return templates.TemplateResponse("health.html", context)


@app.get("/health-data", response_class=HTMLResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_health_data(request: Request):
    """HTMX endpoint for health status data."""
    components = [
        {"id": "message_bus", "name": "Message Bus"},
        {"id": "agent_heartbeats", "name": "Agent Heartbeats"},
        {"id": "siem_integration", "name": "SIEM Integration"},
    ]
    health_data = []
    for comp in components:
        rand = random.random()
        status = "online"
        if rand < 0.1:
            status = "offline"
        elif rand < 0.2:
            status = "degraded"
        health_data.append(
            {
                "name": comp["name"],
                "status": status,
                "latency": random.randint(10, 100) if status == "online" else "N/A",
            }
        )
    context = {"request": request, "health_data": health_data}
    context.update(get_theme_context(request))
    return templates.TemplateResponse("_health_cards.html", context)


@app.get("/exercises", response_class=HTMLResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def read_exercises(request: Request, db: Session = Depends(get_db)):
    """Exercise listing page."""
    exercises = crud.get_exercises(db)
    templates_data = crud.get_templates(db)

    # Calculate success rate
    completed = sum(1 for ex in exercises if ex.state == 'completed')
    total = len(exercises)
    success_rate = (completed / total * 100) if total > 0 else 0

    context = {
        "request": request,
        "page": "exercises",
        "exercises": exercises,
        "templates": templates_data,
        "success_rate": success_rate,
        "today": datetime.now().strftime("%Y-%m-%d")
    }
    context.update(get_theme_context(request))
    return templates.TemplateResponse("c2_exercises.html", context)


@app.post("/exercise/create")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def create_exercise(
    request: Request,
    template_id: str = Form(...),
    scope: str = Form(default=""),
    db: Session = Depends(get_db),
):
    """Create a new exercise."""
    try:
        # Validate template exists
        template = crud.get_template_by_template_id(db, template_id=template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
            )

        # Generate unique exercise ID
        new_id = f"ex-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}"

        exercise_data = {
            "exercise_id": new_id,
            "template": template_id,
            "state": "draft",
            "progress": 0,
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "owner": "c0nfig",
        }

        crud.create_exercise(db=db, exercise=exercise_data)
        logger.info(f"Created exercise {new_id} from template {template_id}")

        return RedirectResponse(url="/exercises", status_code=303)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create exercise: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create exercise",
        )


# === New Production Exercise API Endpoints ===


@app.post("/api/exercises")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def api_create_exercise(request: Request, db: Session = Depends(get_db)):
    """API endpoint to create a new exercise."""
    try:
        data = await request.json()

        # Validate required fields
        required = ['exercise_id', 'template', 'owner', 'start_date']
        for field in required:
            if field not in data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )

        # Validate template exists
        template = crud.get_template_by_template_id(db, template_id=data['template'])
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )

        # Check for duplicate exercise_id
        existing = crud.get_exercise_by_exercise_id(db, exercise_id=data['exercise_id'])
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Exercise {data['exercise_id']} already exists"
            )

        exercise_data = {
            "exercise_id": data['exercise_id'],
            "template": data['template'],
            "state": data.get('state', 'draft'),
            "progress": data.get('progress', 0),
            "start_date": data['start_date'],
            "owner": data['owner'],
        }

        new_exercise = crud.create_exercise(db=db, exercise=exercise_data)
        logger.info(f"Created exercise {new_exercise.exercise_id} via API")

        return JSONResponse(
            status_code=201,
            content={"success": True, "exercise_id": new_exercise.exercise_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create exercise via API: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/exercises/{exercise_id}/details")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_exercise_details(request: Request, exercise_id: str, db: Session = Depends(get_db)):
    """Get detailed exercise information including linked attack containers."""
    exercise = crud.get_exercise_by_exercise_id(db, exercise_id=exercise_id)
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exercise {exercise_id} not found"
        )

    # Get linked attack containers
    containers = crud.get_attack_containers(db, exercise_id=exercise_id)

    return {
        "success": True,
        "exercise": {
            "exercise_id": exercise.exercise_id,
            "template": exercise.template,
            "state": exercise.state,
            "progress": exercise.progress,
            "start_date": str(exercise.start_date),
            "owner": exercise.owner,
        },
        "containers": [
            {
                "container_id": c.container_id,
                "container_name": c.container_name,
                "attack_type": c.attack_type,
                "target": c.target,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in containers
        ]
    }


@app.patch("/api/exercises/{exercise_id}/state")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def update_exercise_state(
    request: Request,
    exercise_id: str,
    db: Session = Depends(get_db)
):
    """Update exercise state (draft → active → completed/aborted)."""
    try:
        data = await request.json()
        new_state = data.get('state')

        if not new_state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing 'state' field"
            )

        valid_states = ['draft', 'active', 'completed', 'aborted']
        if new_state not in valid_states:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid state. Must be one of: {valid_states}"
            )

        exercise = crud.get_exercise_by_exercise_id(db, exercise_id=exercise_id)
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Exercise {exercise_id} not found"
            )

        # Update state
        exercise.state = new_state

        # Auto-update progress based on state
        if new_state == 'completed':
            exercise.progress = 100
        elif new_state == 'active' and exercise.progress == 0:
            exercise.progress = 10

        db.commit()
        db.refresh(exercise)

        logger.info(f"Updated exercise {exercise_id} state to {new_state}")

        return {
            "success": True,
            "exercise_id": exercise.exercise_id,
            "state": exercise.state,
            "progress": exercise.progress
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update exercise state: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/exercises/{exercise_id}/report")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def download_exercise_report(
    request: Request,
    exercise_id: str,
    db: Session = Depends(get_db)
):
    """Generate and download exercise report as JSON."""
    exercise = crud.get_exercise_by_exercise_id(db, exercise_id=exercise_id)
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exercise {exercise_id} not found"
        )

    # Get template details
    template = crud.get_template_by_template_id(db, template_id=exercise.template)

    # Get linked attack containers
    containers = crud.get_attack_containers(db, exercise_id=exercise_id)

    report = {
        "report_generated": datetime.utcnow().isoformat(),
        "exercise": {
            "exercise_id": exercise.exercise_id,
            "template": exercise.template,
            "template_name": template.name if template else "Unknown",
            "state": exercise.state,
            "progress": exercise.progress,
            "start_date": str(exercise.start_date),
            "owner": exercise.owner,
        },
        "template_details": {
            "name": template.name if template else "Unknown",
            "category": template.category if template else None,
            "risk_level": template.risk_level if template else None,
            "duration": template.duration if template else None,
        } if template else None,
        "attack_operations": [
            {
                "container_id": c.container_id,
                "container_name": c.container_name,
                "attack_type": c.attack_type,
                "target": c.target,
                "status": c.status,
                "command": c.command,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "stopped_at": c.stopped_at.isoformat() if c.stopped_at else None,
            }
            for c in containers
        ],
        "statistics": {
            "total_operations": len(containers),
            "running_operations": sum(1 for c in containers if c.status == 'running'),
            "completed_operations": sum(1 for c in containers if c.status in ['exited', 'stopped']),
        }
    }

    import json
    return JSONResponse(
        content=report,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=exercise-{exercise_id}-report.json"}
    )


@app.get("/templates", response_class=HTMLResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def read_templates(request: Request, db: Session = Depends(get_db)):
    """Template listing page."""
    templates_data = crud.get_templates(db)
    context = {"request": request, "page": "templates", "templates": templates_data}
    context.update(get_theme_context(request))
    return templates.TemplateResponse("c2_templates.html", context)


@app.get("/exercise/create/{template_id}", response_class=HTMLResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def show_create_exercise_form(
    request: Request, template_id: str, db: Session = Depends(get_db)
):
    """Exercise creation form."""
    template = crud.get_template_by_template_id(db, template_id=template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )
    context = {"request": request, "template": template}
    context.update(get_theme_context(request))
    return templates.TemplateResponse("c2_create_exercise.html", context)


@app.get("/metrics", response_class=HTMLResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def read_metrics(request: Request):
    """Metrics dashboard page."""
    context = {"request": request, "page": "metrics"}
    context.update(get_theme_context(request))
    return templates.TemplateResponse("metrics.html", context)


@app.get("/metrics/dashboard", response_class=HTMLResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def read_metrics_dashboard(request: Request):
    """Comprehensive metrics analytics dashboard."""
    context = {"request": request, "page": "metrics"}
    context.update(get_theme_context(request))
    return templates.TemplateResponse("metrics_dashboard.html", context)


@app.get("/metrics-chart", response_class=HTMLResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_metrics_chart(request: Request, db: Session = Depends(get_db)):
    """HTMX endpoint for metrics chart data."""
    exercises = crud.get_exercises(db)
    templates_data = crud.get_templates(db)

    template_map = {t.template_id: t.category for t in templates_data}
    
    category_metrics = {}

    for ex in exercises:
        category = template_map.get(ex.template)
        if category:
            if category not in category_metrics:
                category_metrics[category] = {"completed": 0, "total": 0}
            
            category_metrics[category]["total"] += 1
            if ex.state == "completed":
                category_metrics[category]["completed"] += 1

    chart_data = []
    for category, metrics in category_metrics.items():
        success_rate = (metrics["completed"] / metrics["total"] * 100) if metrics["total"] > 0 else 0
        chart_data.append({"label": category.capitalize(), "value": round(success_rate)})

    context = {"request": request, "data": chart_data}
    context.update(get_theme_context(request))
    return templates.TemplateResponse("_metrics_chart.html", context)


# === Attack Container Management ===


@app.get("/attacks", response_class=HTMLResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def read_attacks(request: Request, db: Session = Depends(get_db)):
    """Attack operations page."""
    containers = crud.get_attack_containers(db)
    exercises = crud.get_exercises(db)
    context = {"request": request, "page": "attacks", "containers": containers, "exercises": exercises}
    context.update(get_theme_context(request))
    return templates.TemplateResponse("attacks.html", context)


@app.post("/api/attacks/nmap")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def launch_nmap_scan(
    request: Request,
    target: str = Form(...),
    scan_type: str = Form(default="quick"),
    exercise_id: str = Form(default=None),
    db: Session = Depends(get_db),
):
    """Launch nmap scan against target."""
    try:
        # Validate input using schema
        from .validators import NmapScanRequest
        validated_data = NmapScanRequest(
            target=target,
            scan_type=scan_type,
            exercise_id=exercise_id
        )

        result = podman_service.nmap_scan(
            target=validated_data.target,
            scan_type=validated_data.scan_type,
            exercise_id=validated_data.exercise_id
        )

        if result["success"]:
            # Record in database
            container_data = {
                "container_id": result["container_id"],
                "container_name": result["container_name"],
                "exercise_id": exercise_id,
                "image": podman_service.kali_image,
                "status": "running",
                "target": validated_data.target,
                "attack_type": "nmap",
                "command": f"nmap scan ({validated_data.scan_type})",
            }
            crud.create_attack_container(db, container_data)

            logger.info(f"Nmap scan launched: {result['container_id']} -> {validated_data.target}")
            return JSONResponse({"success": True, "data": result})
        else:
            logger.error(f"Nmap scan failed: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get("error"))

    except ValueError as e:
        logger.error(f"Invalid nmap request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to launch nmap scan: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/attacks/metasploit")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def launch_metasploit(
    request: Request,
    target: str = Form(...),
    exercise_id: str = Form(default=None),
    db: Session = Depends(get_db),
):
    """Launch Metasploit container."""
    try:
        # Validate input using schema
        from .validators import MetasploitRequest
        validated_data = MetasploitRequest(
            target=target,
            exercise_id=exercise_id
        )

        result = podman_service.metasploit_console(
            target=validated_data.target,
            exercise_id=validated_data.exercise_id
        )

        if result["success"]:
            container_data = {
                "container_id": result["container_id"],
                "container_name": result["container_name"],
                "exercise_id": exercise_id,
                "image": podman_service.kali_image,
                "status": "running",
                "target": validated_data.target,
                "attack_type": "metasploit",
                "command": "msfconsole",
            }
            crud.create_attack_container(db, container_data)

            logger.info(f"Metasploit launched: {result['container_id']} -> {validated_data.target}")
            return JSONResponse({"success": True, "data": result})
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))

    except ValueError as e:
        logger.error(f"Invalid metasploit request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to launch Metasploit: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/attacks/sqlmap")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def launch_sqlmap(
    request: Request,
    target: str = Form(...),
    exercise_id: str = Form(default=None),
    db: Session = Depends(get_db),
):
    """Launch SQLMap container."""
    try:
        # Validate input using schema
        from .validators import SQLMapRequest
        validated_data = SQLMapRequest(
            target=target,
            exercise_id=exercise_id
        )

        result = podman_service.sql_injection_test(
            target=validated_data.target,
            exercise_id=validated_data.exercise_id
        )

        if result["success"]:
            container_data = {
                "container_id": result["container_id"],
                "container_name": result["container_name"],
                "exercise_id": exercise_id,
                "image": podman_service.kali_image,
                "status": "running",
                "target": validated_data.target,
                "attack_type": "sqlmap",
                "command": "sqlmap",
            }
            crud.create_attack_container(db, container_data)

            logger.info(f"SQLMap launched: {result['container_id']} -> {validated_data.target}")
            return JSONResponse({"success": True, "data": result})
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))

    except ValueError as e:
        logger.error(f"Invalid sqlmap request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to launch SQLMap: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/attacks/custom")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def launch_custom_attack(
    request: Request,
    target: str = Form(...),
    command: str = Form(...),
    attack_type: str = Form(default="custom"),
    exercise_id: str = Form(default=None),
    allow_complex: bool = Form(default=False),
    db: Session = Depends(get_db),
):
    """Launch custom attack container."""
    try:
        # Validate input using schema
        from .validators import CustomAttackRequest
        validated_data = CustomAttackRequest(
            target=target,
            command=command,
            attack_type=attack_type,
            exercise_id=exercise_id,
            allow_complex=allow_complex
        )

        result = podman_service.custom_attack(
            target=validated_data.target,
            command=validated_data.command,
            attack_type=validated_data.attack_type,
            exercise_id=validated_data.exercise_id,
            allow_complex=validated_data.allow_complex
        )

        if result["success"]:
            container_data = {
                "container_id": result["container_id"],
                "container_name": result["container_name"],
                "exercise_id": exercise_id,
                "image": podman_service.kali_image,
                "status": "running",
                "target": validated_data.target,
                "attack_type": validated_data.attack_type,
                "command": validated_data.command,
            }
            crud.create_attack_container(db, container_data)

            logger.info(f"Custom attack launched: {result['container_id']} -> {validated_data.target}")
            return JSONResponse({"success": True, "data": result})
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))

    except ValueError as e:
        logger.error(f"Invalid custom attack request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to launch custom attack: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/attacks/containers")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def list_containers(
    request: Request,
    exercise_id: str = None,
    db: Session = Depends(get_db),
):
    """List all attack containers."""
    containers = crud.get_attack_containers(db, exercise_id=exercise_id)
    return JSONResponse({
        "success": True,
        "containers": [
            {
                "id": c.id,
                "container_id": c.container_id,
                "container_name": c.container_name,
                "exercise_id": c.exercise_id,
                "target": c.target,
                "attack_type": c.attack_type,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in containers
        ]
    })


@app.get("/api/attacks/containers/{container_id}/logs")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_container_logs(
    request: Request,
    container_id: str,
    tail: int = 100,
):
    """Get logs from attack container."""
    result = podman_service.get_container_logs(container_id, tail=tail)

    if result["success"]:
        return JSONResponse({"success": True, "logs": result["logs"]})
    else:
        raise HTTPException(status_code=404, detail=result.get("error"))


@app.post("/api/attacks/containers/{container_id}/stop")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def stop_container(
    request: Request,
    container_id: str,
    db: Session = Depends(get_db),
):
    """Stop attack container."""
    result = podman_service.stop_container(container_id)

    if result["success"]:
        crud.update_attack_container_status(db, container_id, "stopped")
        logger.info(f"Container stopped: {container_id}")
        return JSONResponse({"success": True, "message": result["message"]})
    else:
        raise HTTPException(status_code=500, detail=result.get("error"))


@app.delete("/api/attacks/containers/{container_id}")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def delete_container(
    request: Request,
    container_id: str,
    db: Session = Depends(get_db),
):
    """Remove attack container."""
    result = podman_service.remove_container(container_id, force=True)

    if result["success"]:
        crud.delete_attack_container(db, container_id)
        logger.info(f"Container removed: {container_id}")
        return JSONResponse({"success": True, "message": result["message"]})
    else:
        raise HTTPException(status_code=500, detail=result.get("error"))


# === WebSocket Terminal Endpoint ===


@app.websocket("/ws/terminal/{container_id}")
async def websocket_terminal(websocket: WebSocket, container_id: str):
    """WebSocket endpoint for real-time container terminal output."""
    await terminal_streamer.connect(websocket, container_id)

    try:
        # Send welcome message
        await websocket.send_text(f"\r\n\x1b[32m[*] Connected to container: {container_id}\x1b[0m\r\n\r\n")

        # Start streaming logs
        await terminal_streamer.stream_container_logs(websocket, container_id, follow=True)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for container: {container_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        terminal_streamer.disconnect(websocket, container_id)


# === WebSocket Chain Execution Monitor Endpoint ===


@app.websocket("/ws/chain-execution/{execution_id}")
async def websocket_chain_execution(websocket: WebSocket, execution_id: str):
    """WebSocket endpoint for real-time chain execution monitoring."""
    await chain_monitor.connect(websocket, execution_id)

    try:
        # Start monitoring task
        await chain_monitor.start_monitoring(execution_id, websocket)

        # Handle incoming client messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                await chain_monitor.handle_client_message(execution_id, message)
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for execution: {execution_id}")
                break
            except Exception as e:
                logger.error(f"Error handling client message: {e}")
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for execution: {execution_id}")
    except Exception as e:
        logger.error(f"WebSocket error for execution {execution_id}: {e}")
    finally:
        chain_monitor.disconnect(websocket, execution_id)


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler."""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=404, content={"detail": "Endpoint not found"}
        )
    context = {
        "request": request,
        "status_code": 404,
        "error_title": "Page Not Found",
        "detail": "The page you're looking for doesn't exist.",
        "page": "error"
    }
    context.update(get_theme_context(request))
    return templates.TemplateResponse("error.html", context, status_code=404)


@app.exception_handler(500)
async def server_error_handler(request: Request, exc: Exception):
    """Custom 500 handler."""
    logger.error(f"Internal server error: {exc}", exc_info=True)
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
    context = {
        "request": request,
        "status_code": 500,
        "error_title": "Internal Server Error",
        "detail": "Something went wrong on our end.",
        "page": "error"
    }
    context.update(get_theme_context(request))
    return templates.TemplateResponse("error.html", context, status_code=500)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS,
    )
