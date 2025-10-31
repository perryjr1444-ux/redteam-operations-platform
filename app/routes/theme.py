"""
Theme API Routes
Provides endpoints for theme switching and management
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
from pydantic import BaseModel

from ..theme import theme_manager, Theme

router = APIRouter(prefix="/api/theme", tags=["theme"])


class ThemeChangeRequest(BaseModel):
    """Request model for theme change"""
    theme: str


@router.get("")
async def get_current_theme(request: Request) -> Dict[str, Any]:
    """
    Get current active theme

    Returns:
        {
            "theme": "shadcn",
            "name": "Shadcn",
            "description": "Clean, minimal, professional",
            "dark_mode": true
        }
    """
    current_theme = theme_manager.get_theme(request)
    theme_config = theme_manager.get_theme_config(current_theme)

    return {
        "theme": current_theme.value,
        "name": theme_config["name"],
        "description": theme_config["description"],
        "dark_mode": theme_config["dark_mode"]
    }


@router.get("/list")
async def list_themes() -> Dict[str, Any]:
    """
    List all available themes

    Returns:
        {
            "themes": [
                {
                    "value": "shadcn",
                    "name": "Shadcn",
                    "description": "Clean, minimal, professional",
                    "dark_mode": true
                },
                ...
            ]
        }
    """
    all_themes = theme_manager.get_all_themes()

    themes_list = [
        {
            "value": theme_value,
            "name": config["name"],
            "description": config["description"],
            "dark_mode": config["dark_mode"]
        }
        for theme_value, config in all_themes.items()
    ]

    return {"themes": themes_list}


@router.post("")
async def set_theme(request: Request, theme_data: ThemeChangeRequest) -> Dict[str, Any]:
    """
    Set/switch theme

    Request body:
        {
            "theme": "shadcn" | "cyberpunk" | "military"
        }

    Returns:
        {
            "success": true,
            "theme": "shadcn",
            "message": "Theme changed to Shadcn"
        }
    """
    # Validate theme
    try:
        new_theme = Theme(theme_data.theme)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid theme: {theme_data.theme}. Valid options: {[t.value for t in Theme]}"
        )

    # Set theme in session
    theme_manager.set_theme(request, new_theme)

    theme_config = theme_manager.get_theme_config(new_theme)

    response = JSONResponse(content={
        "success": True,
        "theme": new_theme.value,
        "name": theme_config["name"],
        "message": f"Theme changed to {theme_config['name']}"
    })

    # Also set cookie as fallback
    response.set_cookie(
        key="theme",
        value=new_theme.value,
        max_age=31536000,  # 1 year
        httponly=False,  # Accessible by JavaScript
        samesite="lax"
    )

    return response


@router.delete("")
async def reset_theme(request: Request) -> Dict[str, Any]:
    """
    Reset theme to default

    Returns:
        {
            "success": true,
            "theme": "shadcn",
            "message": "Theme reset to default"
        }
    """
    # Clear session
    if hasattr(request, "session") and "theme" in request.session:
        del request.session["theme"]

    default_theme = theme_manager.default_theme
    theme_config = theme_manager.get_theme_config(default_theme)

    response = JSONResponse(content={
        "success": True,
        "theme": default_theme.value,
        "name": theme_config["name"],
        "message": "Theme reset to default"
    })

    # Clear cookie
    response.delete_cookie("theme")

    return response
