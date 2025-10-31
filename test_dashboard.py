#!/usr/bin/env python3
"""
Test script for Execution Monitor Dashboard
Verifies that all components are properly integrated
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_files_exist():
    """Test that all required files exist"""
    print("\n=== Testing File Existence ===")

    files = {
        "Template": "templates/execution_dashboard.html",
        "JavaScript": "static/js/execution-dashboard.js",
        "UI Routes": "app/routes/ui_enhanced.py",
        "API Routes": "app/routes/api_enhanced.py",
        "Alpine Components": "static/js/alpine-components.js",
        "Documentation": "EXECUTION_DASHBOARD.md"
    }

    all_exist = True
    for name, path in files.items():
        full_path = project_root / path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"  ✓ {name}: {path} ({size:,} bytes)")
        else:
            print(f"  ✗ {name}: {path} NOT FOUND")
            all_exist = False

    return all_exist


def test_imports():
    """Test that Python imports work"""
    print("\n=== Testing Python Imports ===")

    try:
        from app.routes.api_enhanced import router as api_router
        print("  ✓ api_enhanced imports successfully")

        from app.routes.ui_enhanced import router as ui_router
        print("  ✓ ui_enhanced imports successfully")

        from app.fractal_orchestrator import FractalOrchestrator, ExecutionNode
        print("  ✓ fractal_orchestrator imports successfully")

        return True
    except Exception as e:
        print(f"  ✗ Import error: {e}")
        return False


def test_api_routes():
    """Test that API routes are defined"""
    print("\n=== Testing API Routes ===")

    try:
        from app.routes.api_enhanced import router

        # Check for required routes
        required_routes = [
            "/api/execution/active",
            "/api/execution/tree/{root_id}",
            "/api/metrics/live",
            "/api/ai/agents/status"
        ]

        # Get all route paths
        route_paths = [route.path for route in router.routes]

        all_found = True
        for required in required_routes:
            # Check if route exists (handle path parameters)
            base_path = required.replace("{root_id}", "")
            found = any(base_path in path for path in route_paths)

            if found:
                print(f"  ✓ {required}")
            else:
                print(f"  ✗ {required} NOT FOUND")
                all_found = False

        return all_found
    except Exception as e:
        print(f"  ✗ Error checking routes: {e}")
        return False


def test_ui_routes():
    """Test that UI routes are defined"""
    print("\n=== Testing UI Routes ===")

    try:
        from app.routes.ui_enhanced import router

        # Check for execution monitor route
        route_paths = [route.path for route in router.routes]

        if "/execution/monitor" in route_paths:
            print("  ✓ /execution/monitor")
            return True
        else:
            print("  ✗ /execution/monitor NOT FOUND")
            return False
    except Exception as e:
        print(f"  ✗ Error checking routes: {e}")
        return False


def test_template_syntax():
    """Test template for basic syntax errors"""
    print("\n=== Testing Template Syntax ===")

    try:
        template_path = project_root / "templates" / "execution_dashboard.html"
        content = template_path.read_text()

        # Check for required elements
        required_elements = [
            "executionDashboard()",
            "activeExecutions",
            "metrics",
            "resources",
            "timeline",
            "logs",
            "performanceChart",
            "statusChart"
        ]

        all_found = True
        for element in required_elements:
            if element in content:
                print(f"  ✓ Contains '{element}'")
            else:
                print(f"  ✗ Missing '{element}'")
                all_found = False

        return all_found
    except Exception as e:
        print(f"  ✗ Error checking template: {e}")
        return False


def test_javascript_syntax():
    """Test JavaScript for basic syntax"""
    print("\n=== Testing JavaScript Syntax ===")

    try:
        js_path = project_root / "static" / "js" / "execution-dashboard.js"
        content = js_path.read_text()

        # Check for required functions
        required_functions = [
            "executionDashboard()",
            "fetchActiveExecutions",
            "fetchMetrics",
            "connectWebSocket",
            "handleWebSocketMessage",
            "pauseExecution",
            "resumeExecution",
            "cancelExecution"
        ]

        all_found = True
        for func in required_functions:
            if func in content:
                print(f"  ✓ Contains '{func}'")
            else:
                print(f"  ✗ Missing '{func}'")
                all_found = False

        return all_found
    except Exception as e:
        print(f"  ✗ Error checking JavaScript: {e}")
        return False


def test_alpine_store():
    """Test Alpine.js store configuration"""
    print("\n=== Testing Alpine.js Store ===")

    try:
        alpine_path = project_root / "static" / "js" / "alpine-components.js"
        content = alpine_path.read_text()

        # Check for execution store
        if "Alpine.store('execution'" in content:
            print("  ✓ Execution store defined")
        else:
            print("  ✗ Execution store NOT FOUND")
            return False

        # Check for required store properties
        required_props = [
            "activeExecutions",
            "completedToday",
            "avgDuration",
            "fetch()",
            "startAutoRefresh"
        ]

        all_found = True
        for prop in required_props:
            if prop in content:
                print(f"  ✓ Store has '{prop}'")
            else:
                print(f"  ✗ Store missing '{prop}'")
                all_found = False

        return all_found
    except Exception as e:
        print(f"  ✗ Error checking Alpine store: {e}")
        return False


def test_orchestrator_integration():
    """Test FractalOrchestrator integration"""
    print("\n=== Testing Orchestrator Integration ===")

    try:
        from app.fractal_orchestrator import (
            FractalOrchestrator,
            ExecutionNode,
            ExecutionLevel,
            ExecutionStatus
        )

        # Create orchestrator
        orchestrator = FractalOrchestrator()
        print("  ✓ FractalOrchestrator instantiated")

        # Create test node
        node = ExecutionNode(
            id="test_exec_001",
            level=ExecutionLevel.EXERCISE,
            type="test_exercise",
            name="Test Exercise"
        )
        print("  ✓ ExecutionNode created")

        # Register node
        orchestrator.register_node(node)
        print("  ✓ Node registered in orchestrator")

        # Retrieve node
        retrieved = orchestrator.get_node("test_exec_001")
        if retrieved and retrieved.id == node.id:
            print("  ✓ Node retrieved successfully")
        else:
            print("  ✗ Node retrieval failed")
            return False

        return True
    except Exception as e:
        print(f"  ✗ Error testing orchestrator: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("EXECUTION MONITOR DASHBOARD - TEST SUITE")
    print("="*60)

    results = {
        "Files Exist": test_files_exist(),
        "Python Imports": test_imports(),
        "API Routes": test_api_routes(),
        "UI Routes": test_ui_routes(),
        "Template Syntax": test_template_syntax(),
        "JavaScript Syntax": test_javascript_syntax(),
        "Alpine Store": test_alpine_store(),
        "Orchestrator Integration": test_orchestrator_integration()
    }

    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")

    print("\n" + "-"*60)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ ALL TESTS PASSED! Dashboard is ready to use.")
        print("\nAccess the dashboard at: http://localhost:8000/execution/monitor")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
