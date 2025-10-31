"""
Test suite for Metrics Analytics Dashboard
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import json


def test_metrics_dashboard_route(client: TestClient):
    """Test metrics dashboard page loads successfully"""
    response = client.get("/metrics/dashboard")

    assert response.status_code == 200
    assert b"Metrics Analytics Dashboard" in response.content
    assert b"metrics-dashboard.js" in response.content
    assert b"Chart.js" in response.content


def test_metrics_live_endpoint(client: TestClient):
    """Test /api/metrics/live endpoint"""
    response = client.get("/api/metrics/live")

    assert response.status_code == 200

    data = response.json()
    assert "active_exercises" in data
    assert "system_health" in data
    assert "running_containers" in data
    assert "uptime" in data
    assert "timestamp" in data

    # Validate data types
    assert isinstance(data["active_exercises"], int)
    assert isinstance(data["system_health"], int)
    assert isinstance(data["running_containers"], int)
    assert isinstance(data["uptime"], str)
    assert isinstance(data["timestamp"], str)

    # Validate ranges
    assert 0 <= data["system_health"] <= 100
    assert data["active_exercises"] >= 0
    assert data["running_containers"] >= 0


def test_metrics_activity_endpoint(client: TestClient):
    """Test /api/metrics/activity endpoint"""
    response = client.get("/api/metrics/activity")

    assert response.status_code == 200

    data = response.json()
    assert "completed_operations" in data
    assert "total_operations" in data
    assert "operation_status" in data
    assert "tool_usage" in data
    assert "recent_activity" in data
    assert "timeline" in data

    # Validate operation status structure
    status = data["operation_status"]
    assert "success" in status
    assert "failed" in status
    assert "pending" in status

    # Validate tool usage is a dictionary
    assert isinstance(data["tool_usage"], dict)

    # Validate recent activity is a list
    assert isinstance(data["recent_activity"], list)

    # Validate timeline structure
    timeline = data["timeline"]
    assert "labels" in timeline
    assert "values" in timeline
    assert isinstance(timeline["labels"], list)
    assert isinstance(timeline["values"], list)
    assert len(timeline["labels"]) == len(timeline["values"])


def test_activity_log_structure(client: TestClient):
    """Test recent activity log has correct structure"""
    response = client.get("/api/metrics/activity")
    data = response.json()

    if len(data["recent_activity"]) > 0:
        activity = data["recent_activity"][0]

        assert "type" in activity
        assert "message" in activity
        assert "details" in activity
        assert "timestamp" in activity

        # Validate timestamp format
        try:
            datetime.fromisoformat(activity["timestamp"])
        except ValueError:
            pytest.fail("Invalid timestamp format")


def test_tool_usage_data(client: TestClient):
    """Test tool usage data contains expected tools"""
    response = client.get("/api/metrics/activity")
    data = response.json()

    tool_usage = data["tool_usage"]

    # Check for common tools
    expected_tools = ["nmap", "sqlmap", "metasploit", "nikto", "gobuster"]

    for tool in expected_tools:
        if tool in tool_usage:
            assert isinstance(tool_usage[tool], int)
            assert tool_usage[tool] >= 0


def test_metrics_dashboard_components(client: TestClient):
    """Test dashboard contains all required components"""
    response = client.get("/metrics/dashboard")
    content = response.content.decode()

    # Check for key dashboard components
    assert "performanceChart" in content
    assert "successRateChart" in content
    assert "toolUsageChart" in content
    assert "activityChart" in content
    assert "resourceChart" in content

    # Check for time range selectors
    assert "1 Hour" in content or "1h" in content
    assert "24 Hours" in content or "24h" in content
    assert "7 Days" in content or "7d" in content
    assert "30 Days" in content or "30d" in content

    # Check for export buttons
    assert "Export CSV" in content
    assert "Export JSON" in content


def test_metrics_dashboard_alpine_component(client: TestClient):
    """Test Alpine.js component is properly loaded"""
    response = client.get("/static/js/metrics-dashboard.js")

    assert response.status_code == 200

    content = response.content.decode()

    # Check for key Alpine component functions
    assert "metricsDashboard" in content
    assert "fetchLiveMetrics" in content
    assert "fetchActivityData" in content
    assert "initializeCharts" in content
    assert "exportData" in content

    # Check for Chart.js configuration
    assert "Chart.defaults" in content
    assert "chartTheme" in content


def test_operation_status_totals(client: TestClient):
    """Test operation status numbers add up correctly"""
    response = client.get("/api/metrics/activity")
    data = response.json()

    status = data["operation_status"]
    total = data["total_operations"]
    completed = data["completed_operations"]

    # Success + failed should equal completed
    assert status["success"] + status["failed"] == completed

    # Completed + pending should equal total
    assert completed + status["pending"] == total


def test_timeline_data_consistency(client: TestClient):
    """Test timeline data is consistent"""
    response = client.get("/api/metrics/activity")
    data = response.json()

    timeline = data["timeline"]

    # Should have 7 days of data
    assert len(timeline["labels"]) == 7
    assert len(timeline["values"]) == 7

    # All values should be non-negative
    for value in timeline["values"]:
        assert value >= 0


def test_metrics_dashboard_auto_refresh_config(client: TestClient):
    """Test auto-refresh configuration in JavaScript"""
    response = client.get("/static/js/metrics-dashboard.js")
    content = response.content.decode()

    # Check for interval definitions
    assert "intervals" in content
    assert "startAutoRefresh" in content

    # Check for reasonable refresh intervals (in comments or code)
    assert "5000" in content or "5 seconds" in content
    assert "10000" in content or "10 seconds" in content
    assert "30000" in content or "30 seconds" in content


def test_export_functionality_present(client: TestClient):
    """Test export functionality is implemented"""
    response = client.get("/static/js/metrics-dashboard.js")
    content = response.content.decode()

    # Check for export functions
    assert "exportData" in content
    assert "downloadJSON" in content
    assert "downloadCSV" in content

    # Check for blob creation (used in downloads)
    assert "Blob" in content
    assert "createObjectURL" in content


def test_chart_theme_configuration(client: TestClient):
    """Test Chart.js theme is properly configured"""
    response = client.get("/static/js/metrics-dashboard.js")
    content = response.content.decode()

    # Check for dark theme colors
    assert "chartTheme" in content

    # Check for Chart.js defaults configuration
    assert "Chart.defaults.color" in content
    assert "Chart.defaults.borderColor" in content
    assert "Chart.defaults.font.family" in content


def test_container_stats_endpoint(client: TestClient):
    """Test container statistics can be retrieved"""
    response = client.get("/api/attacks/containers")

    assert response.status_code == 200

    data = response.json()
    assert "success" in data

    if data["success"]:
        assert "containers" in data
        assert isinstance(data["containers"], list)


def test_metrics_dashboard_responsive_design(client: TestClient):
    """Test dashboard has responsive design classes"""
    response = client.get("/metrics/dashboard")
    content = response.content.decode()

    # Check for Bootstrap responsive grid classes
    assert "col-md-" in content
    assert "row" in content
    assert "g-3" in content or "gutter" in content


def test_activity_log_limit(client: TestClient):
    """Test activity log has reasonable limit"""
    response = client.get("/api/metrics/activity")
    data = response.json()

    activity_log = data["recent_activity"]

    # Should not exceed reasonable limit
    assert len(activity_log) <= 50


def test_health_color_coding(client: TestClient):
    """Test system health has color coding"""
    response = client.get("/metrics/dashboard")
    content = response.content.decode()

    # Check for health color functions/classes
    assert "getHealthColor" in content or "text-success" in content
    assert "text-warning" in content
    assert "text-danger" in content


def test_chart_initialization(client: TestClient):
    """Test all charts are initialized"""
    response = client.get("/static/js/metrics-dashboard.js")
    content = response.content.decode()

    # Check for chart initialization functions
    assert "initPerformanceChart" in content
    assert "initSuccessRateChart" in content
    assert "initToolUsageChart" in content
    assert "initActivityChart" in content
    assert "initResourceChart" in content


def test_time_formatting_functions(client: TestClient):
    """Test time formatting utilities exist"""
    response = client.get("/static/js/metrics-dashboard.js")
    content = response.content.decode()

    # Check for time formatting functions
    assert "formatTime" in content
    assert "calculateUptime" in content


def test_metrics_dashboard_accessibility(client: TestClient):
    """Test dashboard has basic accessibility features"""
    response = client.get("/metrics/dashboard")
    content = response.content.decode()

    # Check for ARIA attributes or semantic HTML
    assert "<canvas" in content  # Charts should use canvas
    assert "<table" in content   # Data should be in tables
    assert "button" in content   # Interactive elements


def test_api_error_handling(client: TestClient):
    """Test API endpoints handle errors gracefully"""
    # Test with potentially invalid requests
    response = client.get("/api/metrics/live")

    # Should return valid JSON even if services aren't fully initialized
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


def test_dashboard_documentation_exists():
    """Test dashboard documentation file exists"""
    import os

    docs_path = "docs/METRICS_DASHBOARD.md"
    assert os.path.exists(docs_path), "Metrics dashboard documentation should exist"

    with open(docs_path, 'r') as f:
        content = f.read()

        # Check for key documentation sections
        assert "Metrics Analytics Dashboard" in content
        assert "API Endpoints" in content
        assert "Features" in content
        assert "Usage Examples" in content
