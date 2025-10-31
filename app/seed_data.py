"""Comprehensive seed data for production deployment."""

from datetime import datetime, timedelta
import random

# Comprehensive Templates
TEMPLATES = [
    {
        "template_id": "phishing_resilience_campaign",
        "name": "Phishing Resilience Campaign",
        "category": "user_awareness",
        "risk_level": "low",
        "duration": "2 weeks"
    },
    {
        "template_id": "apt_emulation_attack_chain",
        "name": "APT Emulation - Full Attack Chain",
        "category": "detection_validation",
        "risk_level": "medium",
        "duration": "1 week"
    },
    {
        "template_id": "network_egress_monitoring",
        "name": "Network Egress Monitoring Test",
        "category": "detection_validation",
        "risk_level": "low",
        "duration": "3 days"
    },
    {
        "template_id": "physical_access_tabletop",
        "name": "Physical Access Tabletop Exercise",
        "category": "physical_security",
        "risk_level": "low",
        "duration": "1 day"
    },
    {
        "template_id": "ransomware_simulation",
        "name": "Ransomware Detection Simulation",
        "category": "detection_validation",
        "risk_level": "high",
        "duration": "5 days"
    },
    {
        "template_id": "lateral_movement_test",
        "name": "Lateral Movement Detection",
        "category": "detection_validation",
        "risk_level": "medium",
        "duration": "4 days"
    },
    {
        "template_id": "credential_harvesting_sim",
        "name": "Credential Harvesting Simulation",
        "category": "user_awareness",
        "risk_level": "medium",
        "duration": "1 week"
    },
    {
        "template_id": "cloud_breach_scenario",
        "name": "Cloud Infrastructure Breach Scenario",
        "category": "detection_validation",
        "risk_level": "high",
        "duration": "2 weeks"
    },
    {
        "template_id": "insider_threat_tabletop",
        "name": "Insider Threat Tabletop Exercise",
        "category": "physical_security",
        "risk_level": "medium",
        "duration": "2 days"
    },
    {
        "template_id": "supply_chain_attack_sim",
        "name": "Supply Chain Attack Simulation",
        "category": "detection_validation",
        "risk_level": "high",
        "duration": "10 days"
    },
    {
        "template_id": "web_app_pentest",
        "name": "Web Application Penetration Test",
        "category": "detection_validation",
        "risk_level": "medium",
        "duration": "1 week"
    },
    {
        "template_id": "social_engineering_vishing",
        "name": "Social Engineering - Vishing Campaign",
        "category": "user_awareness",
        "risk_level": "low",
        "duration": "3 days"
    },
    {
        "template_id": "wireless_security_assessment",
        "name": "Wireless Network Security Assessment",
        "category": "network_monitoring",
        "risk_level": "medium",
        "duration": "5 days"
    },
    {
        "template_id": "data_exfiltration_test",
        "name": "Data Exfiltration Detection Test",
        "category": "detection_validation",
        "risk_level": "medium",
        "duration": "4 days"
    },
    {
        "template_id": "zero_day_response_drill",
        "name": "Zero-Day Response Drill",
        "category": "detection_validation",
        "risk_level": "high",
        "duration": "1 day"
    },
]

# Sample Exercises
EXERCISES = [
    {
        "exercise_id": "ex-20251015-001",
        "template": "apt_emulation_attack_chain",
        "state": "completed",
        "progress": 100,
        "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
        "owner": "c0nfig"
    },
    {
        "exercise_id": "ex-20251105-002",
        "template": "phishing_resilience_campaign",
        "state": "active",
        "progress": 65,
        "start_date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
        "owner": "c0nfig"
    },
    {
        "exercise_id": "ex-20251110-003",
        "template": "ransomware_simulation",
        "state": "draft",
        "progress": 15,
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "owner": "c0nfig"
    },
    {
        "exercise_id": "ex-20251012-004",
        "template": "network_egress_monitoring",
        "state": "completed",
        "progress": 100,
        "start_date": (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d"),
        "owner": "c0nfig"
    },
    {
        "exercise_id": "ex-20251118-005",
        "template": "lateral_movement_test",
        "state": "active",
        "progress": 40,
        "start_date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
        "owner": "c0nfig"
    },
    {
        "exercise_id": "ex-20251120-006",
        "template": "web_app_pentest",
        "state": "draft",
        "progress": 5,
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "owner": "c0nfig"
    },
    {
        "exercise_id": "ex-20251008-007",
        "template": "social_engineering_vishing",
        "state": "completed",
        "progress": 100,
        "start_date": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
        "owner": "c0nfig"
    },
    {
        "exercise_id": "ex-20251115-008",
        "template": "cloud_breach_scenario",
        "state": "active",
        "progress": 25,
        "start_date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
        "owner": "c0nfig"
    },
]
