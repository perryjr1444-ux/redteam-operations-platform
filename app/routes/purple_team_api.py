"""
Purple Team API Routes
Real-time stress test and autonomous learning visualization
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Any
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/purple-team", tags=["purple-team"])

# Templates
templates = Jinja2Templates(directory="templates")

STRESS_TEST_DIR = Path("/home/ubuntu/claude")

@router.get("/status")
async def get_purple_team_status() -> Dict[str, Any]:
    """Get current stress test status and results"""
    try:
        # Find latest iteration file
        iteration_files = sorted(STRESS_TEST_DIR.glob("stress-test-iteration-*.json"))

        if not iteration_files:
            return {
                "status": "no_data",
                "message": "No stress test data found. Run: python3 /home/ubuntu/claude/5-tier-stress-test.py"
            }

        latest_file = iteration_files[-1]
        with open(latest_file) as f:
            data = json.load(f)

        return {
            "status": "active",
            "iteration": data.get("iteration", 0),
            "tier_results": data.get("tier_results", []),
            "analysis": data.get("analysis", {}),
            "performance": data.get("performance", {}),
            "config": data.get("config", {})
        }
    except Exception as e:
        logger.error(f"Error fetching purple team status: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/learning-history")
async def get_learning_history() -> Dict[str, Any]:
    """Get learning loop adaptation history"""
    try:
        learning_files = sorted(STRESS_TEST_DIR.glob("stress-test-learnings-*.json"))

        history = []
        for file in learning_files:
            with open(file) as f:
                history.append(json.load(f))

        return {
            "total_iterations": len(history),
            "learnings": history
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# HTML Dashboard Route
@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def purple_team_dashboard(request: Request):
    """Serve purple team visualization dashboard"""
    return templates.TemplateResponse("purple_team_dashboard.html", {"request": request})
