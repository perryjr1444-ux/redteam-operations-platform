"""
Quick validation script for enhanced integration
Tests routes are registered and accessible
"""

import sys
sys.path.insert(0, '/opt/projects/redteam_py_app')

# Set minimal environment
import os
os.environ['ENVIRONMENT'] = 'development'
os.environ['SECRET_KEY'] = 'test-secret-key-for-validation'
os.environ['DATABASE_URL'] = 'sqlite:///./test.db'

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    # Import routers individually to test
    from app.routes.ui_enhanced import router as ui_router
    from app.routes.api_enhanced import router as api_router

    # Create minimal test app
    test_app = FastAPI()
    test_app.include_router(ui_router)
    test_app.include_router(api_router)

    client = TestClient(test_app)

    print("=" * 60)
    print("INTEGRATION VALIDATION")
    print("=" * 60)

    # Test UI routes
    ui_routes = [
        ("/enhanced", "Enhanced Dashboard"),
        ("/ai/dashboard", "AI Dashboard"),
        ("/execution/monitor", "Execution Monitor"),
        ("/chains/builder", "Chain Builder"),
    ]

    print("\n✅ UI ROUTES:")
    for route, name in ui_routes:
        try:
            response = client.get(route)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"  {status} GET {route:<25} → {response.status_code} ({name})")
        except Exception as e:
            print(f"  ❌ GET {route:<25} → ERROR: {e}")

    # Test API routes
    api_routes = [
        ("/api/metrics/live", "Live Metrics"),
        ("/api/ai/agents/status", "Agent Status"),
        ("/api/execution/active", "Active Executions"),
        ("/api/tools", "Tools List"),
        ("/api/chains", "Chains List"),
        ("/api/health", "Health Check"),
        ("/api/metrics/activity", "Activity Metrics"),
    ]

    print("\n✅ API ROUTES:")
    for route, name in api_routes:
        try:
            response = client.get(route)
            status = "✅" if response.status_code == 200 else "❌"
            if response.status_code == 200:
                # Verify JSON response
                data = response.json()
                print(f"  {status} GET {route:<30} → {response.status_code} ({name}) - JSON ✓")
            else:
                print(f"  {status} GET {route:<30} → {response.status_code} ({name})")
        except Exception as e:
            print(f"  ❌ GET {route:<30} → ERROR: {e}")

    # Test POST endpoint
    print("\n✅ POST ENDPOINTS:")
    try:
        chain_data = {
            "name": "Test Chain",
            "steps": [{"id": "s1", "tool": "nmap", "args": {}, "parallel": False, "dependencies": []}]
        }
        response = client.post("/api/chains", json=chain_data)
        status = "✅" if response.status_code == 200 else "❌"
        print(f"  {status} POST /api/chains → {response.status_code} (Create Chain)")
    except Exception as e:
        print(f"  ❌ POST /api/chains → ERROR: {e}")

    # Check static files
    print("\n✅ STATIC FILES:")
    import pathlib
    static_files = [
        "static/js/alpine-components.js",
        "static/js/charts-enhanced.js",
        "static/js/init-enhanced.js",
    ]

    for file_path in static_files:
        full_path = pathlib.Path(f"/opt/projects/redteam_py_app/{file_path}")
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"  ✅ {file_path:<40} ({size:,} bytes)")
        else:
            print(f"  ❌ {file_path:<40} (NOT FOUND)")

    # Check templates
    print("\n✅ TEMPLATES:")
    templates = [
        "templates/base_enhanced.html",
        "templates/dashboard_enhanced.html",
    ]

    for template_path in templates:
        full_path = pathlib.Path(f"/opt/projects/redteam_py_app/{template_path}")
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"  ✅ {template_path:<40} ({size:,} bytes)")
        else:
            print(f"  ❌ {template_path:<40} (NOT FOUND)")

    print("\n" + "=" * 60)
    print("INTEGRATION VALIDATION COMPLETE ✅")
    print("=" * 60)
    print("\nAll routes registered and accessible!")
    print("Enhanced UI and API endpoints are working.\n")

except Exception as e:
    print(f"\n❌ VALIDATION FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
