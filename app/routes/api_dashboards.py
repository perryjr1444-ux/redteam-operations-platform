"""
Dashboard API Routes for Phase 5.3
Provides 7 specialized endpoints for dashboard data visualization

Endpoints:
- /api/dashboard/agents/status - AI agent status and health
- /api/dashboard/agents/tasks - Agent task queue
- /api/dashboard/execution/tree - 5-layer execution tree
- /api/dashboard/execution/metrics - Execution resource metrics
- /api/dashboard/analytics/mitre - MITRE ATT&CK coverage
- /api/dashboard/analytics/vulnerabilities - Vulnerability data
- /api/dashboard/analytics/posture - Security posture score
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from ..database import get_db
from .. import crud, models

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dashboard", tags=["dashboards"])


# ==================== ENDPOINT 1: AGENT STATUS ====================

@router.get("/agents/status")
async def get_agents_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get all AI agents status, health, and performance metrics

    Returns:
        {
          "agents": [
            {
              "type": "coordinator",
              "status": "healthy",
              "color": "#00ff9f",
              "current_task": "Processing chain optimization",
              "metrics": {
                "tasks_completed": 156,
                "avg_execution_time": 2.3,
                "success_rate": 0.95,
                "queue_length": 3
              }
            },
            // ... 4 more agents
          ],
          "timestamp": "2025-10-22T12:00:00Z"
        }
    """
    try:
        # Mock data for now (replace with real agent data when agent_manager is integrated)
        agents = [
            {
                "type": "coordinator",
                "status": "healthy",
                "color": "#00ff9f",
                "current_task": "Coordinating attack chain execution",
                "metrics": {
                    "tasks_completed": 156,
                    "avg_execution_time": 2.3,
                    "success_rate": 0.95,
                    "queue_length": 3
                }
            },
            {
                "type": "planner",
                "status": "healthy",
                "color": "#ff6b9d",
                "current_task": "Planning reconnaissance phase",
                "metrics": {
                    "tasks_completed": 203,
                    "avg_execution_time": 1.8,
                    "success_rate": 0.92,
                    "queue_length": 5
                }
            },
            {
                "type": "analyzer",
                "status": "healthy",
                "color": "#ffd700",
                "current_task": "Analyzing vulnerability scan results",
                "metrics": {
                    "tasks_completed": 189,
                    "avg_execution_time": 3.1,
                    "success_rate": 0.97,
                    "queue_length": 2
                }
            },
            {
                "type": "advisor",
                "status": "warning",
                "color": "#00d4ff",
                "current_task": "Recommending exploit strategies",
                "metrics": {
                    "tasks_completed": 142,
                    "avg_execution_time": 2.7,
                    "success_rate": 0.89,
                    "queue_length": 8
                }
            },
            {
                "type": "optimizer",
                "status": "healthy",
                "color": "#b794f6",
                "current_task": "Optimizing attack chain performance",
                "metrics": {
                    "tasks_completed": 178,
                    "avg_execution_time": 1.9,
                    "success_rate": 0.94,
                    "queue_length": 4
                }
            }
        ]

        return {
            "agents": agents,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINT 2: AGENT TASKS ====================

@router.get("/agents/tasks")
async def get_agents_tasks(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get agent task queue (pending/running/completed)

    Returns task history and current queue for all agents
    """
    try:
        # Mock task queue data
        now = datetime.utcnow()

        tasks = {
            "pending": [
                {
                    "id": "task_001",
                    "agent": "planner",
                    "priority": "high",
                    "description": "Plan multi-stage web application assessment",
                    "created_at": (now - timedelta(minutes=5)).isoformat()
                },
                {
                    "id": "task_002",
                    "agent": "analyzer",
                    "priority": "medium",
                    "description": "Analyze nmap scan results for vulnerabilities",
                    "created_at": (now - timedelta(minutes=4)).isoformat()
                },
                {
                    "id": "task_003",
                    "agent": "coordinator",
                    "priority": "high",
                    "description": "Coordinate parallel tool execution",
                    "created_at": (now - timedelta(minutes=3)).isoformat()
                },
                {
                    "id": "task_004",
                    "agent": "optimizer",
                    "priority": "low",
                    "description": "Optimize chain execution order",
                    "created_at": (now - timedelta(minutes=2)).isoformat()
                },
            ],
            "running": [
                {
                    "id": "task_005",
                    "agent": "advisor",
                    "priority": "high",
                    "description": "Recommend exploitation techniques for SQLi",
                    "started_at": (now - timedelta(minutes=2)).isoformat(),
                    "progress": 0.65,
                    "estimated_completion": (now + timedelta(minutes=1)).isoformat()
                },
                {
                    "id": "task_006",
                    "agent": "optimizer",
                    "priority": "medium",
                    "description": "Optimize container resource allocation",
                    "started_at": (now - timedelta(minutes=1)).isoformat(),
                    "progress": 0.42,
                    "estimated_completion": (now + timedelta(minutes=2)).isoformat()
                }
            ],
            "completed": [
                {
                    "id": "task_007",
                    "agent": "coordinator",
                    "priority": "high",
                    "description": "Coordinated web reconnaissance chain",
                    "completed_at": (now - timedelta(minutes=6)).isoformat(),
                    "duration": 2.3,
                    "success": True
                },
                {
                    "id": "task_008",
                    "agent": "planner",
                    "priority": "medium",
                    "description": "Planned network discovery phase",
                    "completed_at": (now - timedelta(minutes=8)).isoformat(),
                    "duration": 1.8,
                    "success": True
                },
                {
                    "id": "task_009",
                    "agent": "analyzer",
                    "priority": "high",
                    "description": "Analyzed vulnerability scan data",
                    "completed_at": (now - timedelta(minutes=10)).isoformat(),
                    "duration": 3.1,
                    "success": True
                },
                {
                    "id": "task_010",
                    "agent": "advisor",
                    "priority": "medium",
                    "description": "Recommended SMB exploitation strategy",
                    "completed_at": (now - timedelta(minutes=12)).isoformat(),
                    "duration": 2.7,
                    "success": True
                },
                {
                    "id": "task_011",
                    "agent": "optimizer",
                    "priority": "low",
                    "description": "Optimized chain parallelization",
                    "completed_at": (now - timedelta(minutes=15)).isoformat(),
                    "duration": 1.9,
                    "success": True
                },
            ],
            "total_pending": 4,
            "total_running": 2,
            "total_completed": 156,
            "avg_completion_time": 2.36,
            "success_rate": 0.94
        }

        return tasks
    except Exception as e:
        logger.error(f"Error fetching agent tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINT 3: EXECUTION TREE ====================

@router.get("/execution/tree")
async def get_execution_tree(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get 5-layer execution tree for D3 visualization
    (Meta → Exercise → Chain → Tool → Container)
    """
    try:
        # Build hierarchical tree from database
        # For now, return mock tree structure
        tree = {
            "name": "Meta Execution",
            "layer": "meta",
            "duration": 120.5,
            "status": "completed",
            "color": "#9d4edd",
            "children": [
                {
                    "name": "Exercise: Network Penetration",
                    "layer": "exercise",
                    "duration": 85.2,
                    "status": "completed",
                    "color": "#0096ff",
                    "children": [
                        {
                            "name": "Chain: Recon + Exploit",
                            "layer": "chain",
                            "duration": 65.1,
                            "status": "completed",
                            "color": "#00d9ff",
                            "children": [
                                {
                                    "name": "Tool: nmap",
                                    "layer": "tool",
                                    "duration": 25.3,
                                    "status": "completed",
                                    "color": "#22d3ee",
                                    "children": [
                                        {
                                            "name": "Container: nmap-scan-001",
                                            "layer": "container",
                                            "duration": 25.3,
                                            "status": "completed",
                                            "color": "#06b6d4"
                                        }
                                    ]
                                },
                                {
                                    "name": "Tool: sqlmap",
                                    "layer": "tool",
                                    "duration": 39.8,
                                    "status": "completed",
                                    "color": "#22d3ee",
                                    "children": [
                                        {
                                            "name": "Container: sqlmap-inject-002",
                                            "layer": "container",
                                            "duration": 39.8,
                                            "status": "completed",
                                            "color": "#06b6d4"
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "name": "Chain: Post-Exploitation",
                            "layer": "chain",
                            "duration": 20.1,
                            "status": "running",
                            "color": "#00d9ff",
                            "children": [
                                {
                                    "name": "Tool: metasploit",
                                    "layer": "tool",
                                    "duration": 15.2,
                                    "status": "running",
                                    "color": "#22d3ee",
                                    "children": [
                                        {
                                            "name": "Container: msf-exploit-003",
                                            "layer": "container",
                                            "duration": 15.2,
                                            "status": "running",
                                            "color": "#06b6d4"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    "name": "Exercise: Web App Assessment",
                    "layer": "exercise",
                    "duration": 35.3,
                    "status": "pending",
                    "color": "#0096ff",
                    "children": [
                        {
                            "name": "Chain: Web Reconnaissance",
                            "layer": "chain",
                            "duration": 0,
                            "status": "pending",
                            "color": "#00d9ff",
                            "children": []
                        }
                    ]
                }
            ]
        }

        return tree
    except Exception as e:
        logger.error(f"Error fetching execution tree: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINT 4: EXECUTION METRICS ====================

@router.get("/execution/metrics")
async def get_execution_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get execution metrics (resource utilization, success rates, duration stats)
    """
    try:
        # Get real data from ChainExecution table
        executions = crud.get_chain_executions(db, limit=100)

        # Calculate metrics from real data
        total = len(executions)
        completed = sum(1 for e in executions if e.status == "completed")
        failed = sum(1 for e in executions if e.status == "failed")

        # Calculate success rate
        success_rate = completed / total if total > 0 else 0

        # Calculate duration statistics
        durations = [e.duration for e in executions if e.duration is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        max_duration = max(durations) if durations else 0

        metrics = {
            "resource_utilization": {
                "exercises": {"current": 5, "max": 10, "percentage": 50},
                "chains": {"current": 10, "max": 20, "percentage": 50},
                "tools": {"current": 20, "max": 50, "percentage": 40},
                "containers": {"current": 50, "max": 100, "percentage": 50}
            },
            "success_rates": {
                "overall": round(success_rate, 2) if total > 0 else 0,
                "by_layer": {
                    "meta": 0.95,
                    "exercise": 0.92,
                    "chain": 0.88,
                    "tool": 0.85,
                    "container": 0.82
                }
            },
            "duration_stats": {
                "avg": round(avg_duration, 2),
                "min": round(min_duration, 2),
                "max": round(max_duration, 2),
                "histogram": [10, 15, 25, 30, 12, 8]  # Duration buckets (0-10s, 10-20s, etc.)
            },
            "parallel_efficiency": 0.82,  # 0-1 score
            "bottlenecks": [
                {
                    "layer": "tool",
                    "tool_name": "sqlmap",
                    "avg_duration": 45.2,
                    "severity": "high",
                    "recommendation": "Consider increasing timeout or optimizing crawl depth"
                },
                {
                    "layer": "container",
                    "tool_name": "metasploit",
                    "avg_duration": 32.1,
                    "severity": "medium",
                    "recommendation": "Optimize module loading time"
                }
            ],
            "execution_counts": {
                "total": total,
                "completed": completed,
                "failed": failed,
                "running": sum(1 for e in executions if e.status == "running"),
                "pending": sum(1 for e in executions if e.status == "pending")
            }
        }

        return metrics
    except Exception as e:
        logger.error(f"Error fetching execution metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINT 5: MITRE COVERAGE ====================

@router.get("/analytics/mitre")
async def get_mitre_coverage(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get MITRE ATT&CK coverage matrix (hybrid: real + placeholder)
    Extract tactics/techniques from attack chain templates
    """
    try:
        # Import chain templates
        from ..chains.templates import get_all_templates

        templates = get_all_templates()

        # Extract MITRE tactics from templates
        tactics_coverage = {}
        all_tactics = set()

        for template in templates:
            # Extract MITRE tactics from template
            mitre_tactics = template.mitre_tactics if hasattr(template, 'mitre_tactics') else []

            for tactic in mitre_tactics:
                all_tactics.add(tactic)
                tactics_coverage[tactic] = tactics_coverage.get(tactic, 0) + 1

        # MITRE ATT&CK tactic mapping
        tactic_names = {
            "TA0043": "Reconnaissance",
            "TA0042": "Resource Development",
            "TA0001": "Initial Access",
            "TA0002": "Execution",
            "TA0003": "Persistence",
            "TA0004": "Privilege Escalation",
            "TA0005": "Defense Evasion",
            "TA0006": "Credential Access",
            "TA0007": "Discovery",
            "TA0008": "Lateral Movement",
            "TA0009": "Collection",
            "TA0011": "Command and Control",
            "TA0010": "Exfiltration",
            "TA0040": "Impact"
        }

        # Build tactics list with coverage
        tactics_list = []
        for tactic_id, tactic_name in tactic_names.items():
            coverage_count = tactics_coverage.get(tactic_id, 0)
            tactics_list.append({
                "id": tactic_id,
                "name": tactic_name,
                "coverage_count": coverage_count,
                "has_coverage": coverage_count > 0
            })

        # Mock technique coverage (in production, extract from template metadata)
        techniques = {
            # Reconnaissance
            "T1595": {"name": "Active Scanning", "tactic": "Reconnaissance", "count": 8, "real": True},
            "T1592": {"name": "Gather Victim Host Information", "tactic": "Reconnaissance", "count": 5, "real": True},
            "T1590": {"name": "Gather Victim Network Information", "tactic": "Reconnaissance", "count": 6, "real": True},

            # Initial Access
            "T1190": {"name": "Exploit Public-Facing Application", "tactic": "Initial Access", "count": 4, "real": True},
            "T1566": {"name": "Phishing", "tactic": "Initial Access", "count": 0, "real": False},

            # Credential Access
            "T1110": {"name": "Brute Force", "tactic": "Credential Access", "count": 3, "real": True},
            "T1558": {"name": "Steal or Forge Kerberos Tickets", "tactic": "Credential Access", "count": 2, "real": True},
            "T1003": {"name": "OS Credential Dumping", "tactic": "Credential Access", "count": 5, "real": True},

            # Discovery
            "T1087": {"name": "Account Discovery", "tactic": "Discovery", "count": 4, "real": True},
            "T1046": {"name": "Network Service Discovery", "tactic": "Discovery", "count": 7, "real": True},
            "T1018": {"name": "Remote System Discovery", "tactic": "Discovery", "count": 3, "real": True},

            # Collection
            "T1213": {"name": "Data from Information Repositories", "tactic": "Collection", "count": 2, "real": True},

            # Placeholder techniques (unmapped)
            "T1059": {"name": "Command and Scripting Interpreter", "tactic": "Execution", "count": 0, "real": False},
            "T1547": {"name": "Boot or Logon Autostart Execution", "tactic": "Persistence", "count": 0, "real": False},
            "T1548": {"name": "Abuse Elevation Control Mechanism", "tactic": "Privilege Escalation", "count": 0, "real": False},
        }

        # Count real vs placeholder techniques
        real_techniques = sum(1 for t in techniques.values() if t["real"])
        total_techniques = len(techniques)

        # Coverage percentage
        coverage_percentage = round((real_techniques / total_techniques) * 100, 1) if total_techniques > 0 else 0

        matrix = {
            "tactics": tactics_list,
            "techniques": techniques,
            "summary": {
                "total_tactics": len(tactic_names),
                "covered_tactics": len([t for t in tactics_list if t["has_coverage"]]),
                "total_techniques": total_techniques,
                "covered_techniques": real_techniques,
                "coverage_percentage": coverage_percentage
            },
            "total_real": real_techniques,
            "total_coverage": total_techniques
        }

        return matrix
    except Exception as e:
        logger.error(f"Error fetching MITRE coverage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINT 6: VULNERABILITIES ====================

@router.get("/analytics/vulnerabilities")
async def get_vulnerabilities(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get vulnerability data (CVE list, severity distribution, trends)
    """
    try:
        now = datetime.utcnow()

        vulns = {
            "distribution": {
                "critical": 12,
                "high": 28,
                "medium": 45,
                "low": 67
            },
            "top_vulnerabilities": [
                {
                    "cve_id": "CVE-2024-1234",
                    "severity": "critical",
                    "cvss": 9.8,
                    "title": "Remote Code Execution in Apache Struts",
                    "status": "exploited",
                    "discovered": "2024-10-15",
                    "affected_systems": 3
                },
                {
                    "cve_id": "CVE-2024-5678",
                    "severity": "critical",
                    "cvss": 9.6,
                    "title": "SQL Injection in Web Application",
                    "status": "detected",
                    "discovered": "2024-10-18",
                    "affected_systems": 5
                },
                {
                    "cve_id": "CVE-2024-9012",
                    "severity": "high",
                    "cvss": 8.8,
                    "title": "Privilege Escalation via SMB",
                    "status": "validated",
                    "discovered": "2024-10-20",
                    "affected_systems": 2
                },
                {
                    "cve_id": "CVE-2024-3456",
                    "severity": "high",
                    "cvss": 8.1,
                    "title": "Authentication Bypass in Admin Panel",
                    "status": "detected",
                    "discovered": "2024-10-21",
                    "affected_systems": 1
                },
                {
                    "cve_id": "CVE-2024-7890",
                    "severity": "high",
                    "cvss": 7.5,
                    "title": "Directory Traversal Vulnerability",
                    "status": "detected",
                    "discovered": "2024-10-22",
                    "affected_systems": 4
                },
                {
                    "cve_id": "CVE-2023-4567",
                    "severity": "medium",
                    "cvss": 6.5,
                    "title": "Cross-Site Scripting in Form Handler",
                    "status": "detected",
                    "discovered": "2023-12-10",
                    "affected_systems": 6
                },
                {
                    "cve_id": "CVE-2023-8901",
                    "severity": "medium",
                    "cvss": 5.9,
                    "title": "Information Disclosure via Error Messages",
                    "status": "validated",
                    "discovered": "2023-11-15",
                    "affected_systems": 8
                },
            ],
            "trends": {
                "last_7_days": [15, 18, 22, 19, 24, 21, 28],
                "by_severity": {
                    "critical": [2, 3, 2, 4, 3, 2, 3],
                    "high": [5, 6, 8, 7, 9, 8, 10],
                    "medium": [8, 9, 12, 8, 12, 11, 15]
                },
                "labels": [
                    (now - timedelta(days=6)).strftime("%Y-%m-%d"),
                    (now - timedelta(days=5)).strftime("%Y-%m-%d"),
                    (now - timedelta(days=4)).strftime("%Y-%m-%d"),
                    (now - timedelta(days=3)).strftime("%Y-%m-%d"),
                    (now - timedelta(days=2)).strftime("%Y-%m-%d"),
                    (now - timedelta(days=1)).strftime("%Y-%m-%d"),
                    now.strftime("%Y-%m-%d")
                ]
            },
            "total": 152,
            "exploitable": 15,
            "remediated": 38,
            "pending_validation": 22
        }

        return vulns
    except Exception as e:
        logger.error(f"Error fetching vulnerabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINT 7: SECURITY POSTURE ====================

@router.get("/analytics/posture")
async def get_security_posture(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get overall security posture score and metrics
    """
    try:
        posture = {
            "score": 82,  # 0-100
            "trend": "up",  # up/down/stable
            "trend_percentage": 5.2,  # Percentage change from last period
            "categories": {
                "vulnerability_management": 85,
                "attack_surface": 78,
                "exploit_success": 92,
                "tool_coverage": 88,
                "mitre_coverage": 65,
                "response_time": 90
            },
            "attack_surface": {
                "exposed_services": 12,
                "open_ports": 45,
                "vulnerable_systems": 8,
                "critical_assets": 3,
                "unpatched_systems": 5
            },
            "tool_effectiveness": {
                "nmap": {
                    "success_rate": 0.98,
                    "executions": 156,
                    "avg_duration": 25.3,
                    "findings": 89
                },
                "sqlmap": {
                    "success_rate": 0.76,
                    "executions": 89,
                    "avg_duration": 45.8,
                    "findings": 23
                },
                "metasploit": {
                    "success_rate": 0.82,
                    "executions": 134,
                    "avg_duration": 32.1,
                    "findings": 45
                },
                "gobuster": {
                    "success_rate": 0.91,
                    "executions": 112,
                    "avg_duration": 18.7,
                    "findings": 67
                },
                "nikto": {
                    "success_rate": 0.94,
                    "executions": 98,
                    "avg_duration": 28.5,
                    "findings": 34
                },
                "nuclei": {
                    "success_rate": 0.88,
                    "executions": 145,
                    "avg_duration": 22.4,
                    "findings": 78
                }
            },
            "exploitation_rates": {
                "successful": 78,
                "failed": 22,
                "pending": 5,
                "total_attempts": 105
            },
            "risk_distribution": {
                "critical": 12,
                "high": 28,
                "medium": 45,
                "low": 67,
                "informational": 93
            },
            "compliance": {
                "owasp_top_10": 0.85,
                "pci_dss": 0.72,
                "nist": 0.68,
                "iso_27001": 0.79
            },
            "recommendations": [
                {
                    "priority": "critical",
                    "title": "Patch CVE-2024-1234 in Apache Struts",
                    "impact": "Remote code execution possible",
                    "effort": "low"
                },
                {
                    "priority": "high",
                    "title": "Increase MITRE coverage for Persistence tactics",
                    "impact": "Better detection of persistence mechanisms",
                    "effort": "medium"
                },
                {
                    "priority": "medium",
                    "title": "Optimize SQLMap execution time",
                    "impact": "Faster vulnerability detection",
                    "effort": "low"
                }
            ]
        }

        return posture
    except Exception as e:
        logger.error(f"Error fetching security posture: {e}")
        raise HTTPException(status_code=500, detail=str(e))
