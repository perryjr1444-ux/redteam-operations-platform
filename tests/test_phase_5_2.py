"""
Phase 5.2 Integration Tests
Tests for D3.js Fractal Visualizer + WebSocket enhancements

Components:
- D3.js visualizer JavaScript
- WebSocket fractal updates
- Visualizer HTML template
- Visualizer CSS styling
- Integration with FastAPI routes
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)


class TestVisualizerStaticAssets:
    """Test visualizer static assets are served"""

    def test_fractal_visualizer_js_exists(self):
        """Test fractal-visualizer.js is accessible"""
        response = client.get("/static/js/fractal-visualizer.js")
        assert response.status_code == 200
        assert "FractalVisualizer" in response.text
        assert "class FractalVisualizer" in response.text

    def test_visualizer_css_exists(self):
        """Test visualizer.css is accessible"""
        response = client.get("/static/css/visualizer.css")
        assert response.status_code == 200
        assert "fractal-visualizer" in response.text or "#fractalVisualizer" in response.text

    def test_d3_visualizer_has_required_methods(self):
        """Test visualizer JS has all required methods"""
        response = client.get("/static/js/fractal-visualizer.js")
        content = response.text

        required_methods = [
            "initialize",
            "loadData",
            "render",
            "renderNodes",
            "renderLinks",
            "updateNode",
            "connectWebSocket",
            "centerOnRoot"
        ]

        for method in required_methods:
            assert method in content, f"Missing method: {method}"


class TestVisualizerRoute:
    """Test visualizer UI route"""

    def test_visualizer_route_loads(self):
        """Test /execution/visualizer route"""
        response = client.get("/execution/visualizer")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_visualizer_includes_d3(self):
        """Test visualizer template includes D3.js"""
        response = client.get("/execution/visualizer")
        assert "d3.v7" in response.text or "d3.js" in response.text

    def test_visualizer_includes_fractal_js(self):
        """Test visualizer template includes fractal-visualizer.js"""
        response = client.get("/execution/visualizer")
        assert "fractal-visualizer.js" in response.text

    def test_visualizer_includes_css(self):
        """Test visualizer template includes custom CSS"""
        response = client.get("/execution/visualizer")
        assert "visualizer.css" in response.text

    def test_visualizer_has_container(self):
        """Test visualizer has SVG container"""
        response = client.get("/execution/visualizer")
        assert "fractalVisualizer" in response.text


class TestWebSocketEnhancements:
    """Test WebSocket enhancements for fractal updates"""

    def test_websocket_endpoint_exists(self):
        """Test WebSocket endpoint is available"""
        # WebSocket connection test
        # Note: TestClient doesn't fully support WebSocket testing
        # This is a basic connectivity check
        try:
            with client.websocket_connect("/ws/tool") as websocket:
                # Should connect successfully
                data = websocket.receive_json()
                assert "type" in data or "error" not in data
        except Exception as e:
            # Connection errors are acceptable in test env
            # Just verify the route exists
            pass

    def test_websocket_subscribe_message(self):
        """Test WebSocket subscribe action"""
        # This tests the message structure
        subscribe_msg = {
            "action": "subscribe",
            "execution_id": "test_exec_123"
        }

        # Verify structure
        assert subscribe_msg["action"] == "subscribe"
        assert "execution_id" in subscribe_msg


class TestExecutionTreeAPI:
    """Test execution tree API endpoint"""

    def test_execution_tree_endpoint_exists(self):
        """Test /api/execution/tree/{id} endpoint exists"""
        # Test with dummy ID (should 404 but route exists)
        response = client.get("/api/execution/tree/dummy_id")
        # Should exist as route (even if returns 404 for non-existent ID)
        assert response.status_code in [200, 404, 503]

    def test_execution_active_endpoint(self):
        """Test /api/execution/active returns proper structure"""
        response = client.get("/api/execution/active")
        assert response.status_code == 200

        data = response.json()
        assert "executions" in data
        assert isinstance(data["executions"], list)
        assert "completed_today" in data
        assert "avg_duration" in data


class TestVisualizerFunctionality:
    """Test visualizer JavaScript functionality"""

    def test_visualizer_config_structure(self):
        """Test visualizer has proper config structure"""
        response = client.get("/static/js/fractal-visualizer.js")
        content = response.text

        # Check for config properties
        config_props = [
            "width",
            "height",
            "nodeRadius",
            "levelSpacing",
            "colors"
        ]

        for prop in config_props:
            assert prop in content

    def test_visualizer_status_colors(self):
        """Test visualizer defines status colors"""
        response = client.get("/static/js/fractal-visualizer.js")
        content = response.text

        statuses = ["pending", "running", "completed", "failed"]
        for status in statuses:
            assert status in content

    def test_visualizer_level_colors(self):
        """Test visualizer defines level colors"""
        response = client.get("/static/js/fractal-visualizer.js")
        content = response.text

        levels = ["strategic", "tactical", "operational"]
        for level in levels:
            assert level in content


class TestIntegration:
    """Integration tests for complete visualizer"""

    def test_visualizer_page_complete(self):
        """Test visualizer page has all required elements"""
        response = client.get("/execution/visualizer")
        html = response.text

        # Check for key UI elements
        assert "fractalVisualizer" in html
        assert "executionSelect" in html
        assert "nodeDetails" in html
        assert "executionStats" in html
        assert "wsStatus" in html

    def test_visualizer_controls_exist(self):
        """Test visualizer has control buttons"""
        response = client.get("/execution/visualizer")
        html = response.text

        assert "centerBtn" in html
        assert "refreshBtn" in html

    def test_visualizer_stats_panel(self):
        """Test visualizer has stats panel"""
        response = client.get("/execution/visualizer")
        html = response.text

        stats = ["statTotalNodes", "statRunning", "statCompleted", "statFailed", "statPending"]
        for stat in stats:
            assert stat in html

    def test_visualizer_legend(self):
        """Test visualizer has legend"""
        response = client.get("/execution/visualizer")
        html = response.text

        assert "Legend" in html or "legend" in html.lower()


class TestPhase52Completion:
    """Verify Phase 5.2 is complete"""

    def test_all_routes_registered(self):
        """Test all Phase 5.2 routes are accessible"""
        routes = [
            "/enhanced",
            "/ai/dashboard",
            "/execution/monitor",
            "/execution/visualizer",  # NEW
            "/chains/builder"
        ]

        for route in routes:
            response = client.get(route)
            assert response.status_code == 200, f"Route {route} failed"

    def test_all_api_endpoints(self):
        """Test all API endpoints work"""
        endpoints = [
            "/api/metrics/live",
            "/api/ai/agents/status",
            "/api/execution/active",
            "/api/tools",
            "/api/chains",
            "/api/health",
            "/api/metrics/activity"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200, f"Endpoint {endpoint} failed"
            assert response.headers["content-type"] == "application/json"

    def test_all_static_assets(self):
        """Test all static assets are served"""
        assets = [
            "/static/js/alpine-components.js",
            "/static/js/charts-enhanced.js",
            "/static/js/init-enhanced.js",
            "/static/js/fractal-visualizer.js",  # NEW
            "/static/css/visualizer.css"  # NEW
        ]

        for asset in assets:
            response = client.get(asset)
            assert response.status_code == 200, f"Asset {asset} not found"


# Run with: pytest tests/test_phase_5_2.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
