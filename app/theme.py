"""
Theme Management System
Provides dynamic theme switching with session persistence
"""

from typing import Dict, Optional
from fastapi import Request
from enum import Enum


class Theme(str, Enum):
    """Available UI themes"""
    SHADCN = "shadcn"
    CYBERPUNK = "cyberpunk"
    MILITARY = "military"


# Theme configurations
THEME_CONFIG = {
    Theme.SHADCN: {
        "name": "Shadcn",
        "description": "Clean, minimal, professional",
        "css_files": [
            "/static/css/styles.css",
            "/static/css/shadcn-theme.css"
        ],
        "fonts": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap",
        "dark_mode": True
    },
    Theme.CYBERPUNK: {
        "name": "Cyberpunk",
        "description": "Neon glow, matrix aesthetic",
        "css_files": [
            "/static/css/styles.css",
            "/static/css/custom_theme.css",
            "/static/css/cyberpunk.css"
        ],
        "fonts": "https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto:wght@400;500&family=JetBrains+Mono:wght@400;600&display=swap",
        "dark_mode": True
    },
    Theme.MILITARY: {
        "name": "Military C2",
        "description": "Tactical command & control",
        "css_files": [
            "/static/dist/assets/islands-CJsyTXa3.css"  # Tailwind bundle
        ],
        "fonts": "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;500;600;700&family=Rajdhani:wght@500;700&display=swap",
        "dark_mode": True
    }
}


class ThemeManager:
    """Manages theme selection and configuration"""

    def __init__(self, default_theme: Theme = Theme.SHADCN):
        self.default_theme = default_theme

    def get_theme(self, request: Request) -> Theme:
        """
        Get current theme from session or default

        Priority:
        1. Session (user preference)
        2. Cookie (fallback)
        3. Config default
        4. Fallback to shadcn
        """
        # Check session (only if SessionMiddleware is installed)
        if "session" in request.scope:
            theme_str = request.session.get("theme")
            if theme_str and theme_str in [t.value for t in Theme]:
                return Theme(theme_str)

        # Check cookie fallback
        theme_cookie = request.cookies.get("theme")
        if theme_cookie and theme_cookie in [t.value for t in Theme]:
            return Theme(theme_cookie)

        return self.default_theme

    def set_theme(self, request: Request, theme: Theme):
        """Set theme in session (if SessionMiddleware is installed)"""
        if "session" in request.scope:
            request.session["theme"] = theme.value

    def get_theme_config(self, theme: Theme) -> Dict:
        """Get configuration for a specific theme"""
        return THEME_CONFIG.get(theme, THEME_CONFIG[Theme.SHADCN])

    def get_all_themes(self) -> Dict[str, Dict]:
        """Get all available themes with their configs"""
        return {
            theme.value: {
                **config,
                "value": theme.value
            }
            for theme, config in THEME_CONFIG.items()
        }


# Global theme manager instance
theme_manager = ThemeManager()


def get_theme_context(request: Request) -> Dict:
    """
    Context processor for theme data
    Returns theme configuration for templates
    """
    current_theme = theme_manager.get_theme(request)
    theme_config = theme_manager.get_theme_config(current_theme)

    return {
        "theme": {
            "current": current_theme.value,
            "name": theme_config["name"],
            "description": theme_config["description"],
            "css_files": theme_config["css_files"],
            "fonts": theme_config["fonts"],
            "dark_mode": theme_config["dark_mode"],
            "all_themes": theme_manager.get_all_themes()
        }
    }
