"""
Integration Tests for Enhanced UI Components
Tests the complete integration of FastAPI routes + Alpine.js + API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestEnhancedUIRoutes:
    """Test enhanced UI routes return proper HTML"""

    def test_enhanced_dashboard_loads(self):
        """Test /enhanced dashboard route"""
        response = client.get("/enhanced")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "dashboard_enhanced.html" in response.text or "Red Team" in response.text

    def test_ai_dashboard_loads(self):
        """Test /ai/dashboard route"""
        response = client.get("/ai/dashboard")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_execution_monitor_loads(self):
        """Test /execution/monitor route"""
        response = client.get("/execution/monitor")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_chain_builder_loads(self):
        """Test /chains/builder route"""
        response = client.get("/chains/builder")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestEnhancedAPIEndpoints:
    """Test enhanced API endpoints return proper JSON"""

    def test_metrics_live_endpoint(self):
        """Test /api/metrics/live endpoint"""
        response = client.get("/api/metrics/live")
        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "active_exercises" in data
        assert "system_health" in data
        assert "running_containers" in data
        assert "uptime" in data
        assert "timestamp" in data

        # Check types
        assert isinstance(data["active_exercises"], int)
        assert isinstance(data["system_health"], int)
        assert isinstance(data["running_containers"], int)
        assert isinstance(data["uptime"], str)

        # Check ranges
        assert 0 <= data["system_health"] <= 100

    def test_agents_status_endpoint(self):
        """Test /api/ai/agents/status endpoint"""
        response = client.get("/api/ai/agents/status")
        assert response.status_code == 200
        data = response.json()

        # Check structure
        assert "enabled" in data
        assert "agents" in data
        assert isinstance(data["agents"], dict)

    def test_execution_active_endpoint(self):
        """Test /api/execution/active endpoint"""
        response = client.get("/api/execution/active")
        assert response.status_code == 200
        data = response.json()

        # Check structure
        assert "executions" in data
        assert "completed_today" in data
        assert "avg_duration" in data
        assert isinstance(data["executions"], list)

    def test_tools_endpoint(self):
        """Test /api/tools endpoint"""
        response = client.get("/api/tools")
        assert response.status_code == 200
        data = response.json()

        assert "tools" in data
        assert isinstance(data["tools"], list)

    def test_chains_list_endpoint(self):
        """Test /api/chains GET endpoint"""
        response = client.get("/api/chains")
        assert response.status_code == 200
        data = response.json()

        assert "chains" in data
        assert isinstance(data["chains"], list)

    def test_chains_create_endpoint(self):
        """Test /api/chains POST endpoint"""
        chain_data = {
            "name": "Test Chain",
            "steps": [
                {
                    "id": "step_1",
                    "tool": "nmap",
                    "args": {},
                    "parallel": False,
                    "dependencies": []
                }
            ]
        }

        response = client.post("/api/chains", json=chain_data)
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "chain_id" in data
        assert "message" in data

    def test_chains_create_validation(self):
        """Test /api/chains POST validation"""
        # Missing name
        response = client.post("/api/chains", json={"steps": []})
        assert response.status_code == 400

        # Missing steps
        response = client.post("/api/chains", json={"name": "Test"})
        assert response.status_code == 400

    def test_health_endpoint(self):
        """Test /api/health endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "services" in data

    def test_activity_metrics_endpoint(self):
        """Test /api/metrics/activity endpoint"""
        response = client.get("/api/metrics/activity")
        assert response.status_code == 200
        data = response.json()

        assert "labels" in data
        assert "values" in data
        assert isinstance(data["labels"], list)
        assert isinstance(data["values"], list)


class TestStaticFiles:
    """Test enhanced static files are served"""

    def test_alpine_components_js_served(self):
        """Test alpine-components.js is accessible"""
        response = client.get("/static/js/alpine-components.js")
        assert response.status_code == 200
        assert "Alpine.store" in response.text

    def test_charts_enhanced_js_served(self):
        """Test charts-enhanced.js is accessible"""
        response = client.get("/static/js/charts-enhanced.js")
        assert response.status_code == 200
        assert "StreamingChart" in response.text or "ChartEnhancements" in response.text

    def test_init_enhanced_js_served(self):
        """Test init-enhanced.js is accessible"""
        response = client.get("/static/js/init-enhanced.js")
        assert response.status_code == 200
        assert "startAutoRefresh" in response.text


class TestEndToEnd:
    """End-to-end integration tests"""

    def test_enhanced_dashboard_includes_alpine(self):
        """Test enhanced dashboard includes Alpine.js"""
        response = client.get("/enhanced")
        assert response.status_code == 200

        html = response.text
        # Check for Alpine.js CDN or script tag
        assert "alpinejs" in html.lower() or "x-data" in html

    def test_enhanced_dashboard_includes_stores(self):
        """Test enhanced dashboard references Alpine stores"""
        response = client.get("/enhanced")
        assert response.status_code == 200

        html = response.text
        # Check for store references
        assert "$store.metrics" in html or "$store.agents" in html

    def test_route_collision_check(self):
        """Ensure no route collisions between routers"""
        # All these should work without conflicts
        routes_to_test = [
            "/",  # C2 dashboard
            "/enhanced",  # Enhanced dashboard
            "/api/health",  # Main app health
            "/api/metrics/live",  # Enhanced API
            "/exercises",  # Existing route
        ]

        for route in routes_to_test:
            response = client.get(route)
            assert response.status_code in [200, 404], f"Route {route} failed with {response.status_code}"

    def test_metrics_data_flow(self):
        """Test complete metrics data flow: API -> Store -> UI"""
        # 1. Fetch metrics from API
        api_response = client.get("/api/metrics/live")
        assert api_response.status_code == 200
        metrics = api_response.json()

        # 2. Verify data structure
        assert "active_exercises" in metrics
        assert "system_health" in metrics

        # 3. Verify UI can render (has Alpine binding points)
        ui_response = client.get("/enhanced")
        assert ui_response.status_code == 200
        assert "$store.metrics" in ui_response.text


# Run with: pytest tests/test_integration_enhanced.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
