"""
Intelligent Attack Chain Templates

Pre-built, AI-optimized attack chains for common scenarios.
Templates automatically adapt based on target fingerprinting.

Categories:
- Web Application Assessment
- Network Penetration Testing
- Active Directory Attacks
- Cloud Infrastructure Testing
- Wireless Network Assessment
- Social Engineering Campaigns

Version: 1.0.0
"""

from .templates import get_all_templates, get_template_by_id, get_templates_by_category

__all__ = ["get_all_templates", "get_template_by_id", "get_templates_by_category"]
