"""Test API endpoints."""

import pytest
from fastapi import status


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "healthy"
    assert "version" in data
    assert "timestamp" in data


def test_readiness_probe(client):
    """Test Kubernetes readiness probe."""
    response = client.get("/api/readiness")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ready"}


def test_liveness_probe(client):
    """Test Kubernetes liveness probe."""
    response = client.get("/api/liveness")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "alive"}


def test_root_page(client):
    """Test root dashboard page loads."""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert "text/html" in response.headers["content-type"]


def test_exercises_page(client):
    """Test exercises page loads."""
    response = client.get("/exercises")
    assert response.status_code == status.HTTP_200_OK


def test_templates_page(client):
    """Test templates page loads."""
    response = client.get("/templates")
    assert response.status_code == status.HTTP_200_OK


def test_metrics_page(client):
    """Test metrics page loads."""
    response = client.get("/metrics")
    assert response.status_code == status.HTTP_200_OK


def test_health_page(client):
    """Test health monitoring page loads."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK


def test_404_api(client):
    """Test 404 handling for API routes."""
    response = client.get("/api/nonexistent")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "detail" in data


def test_security_headers(client):
    """Test security headers are present."""
    response = client.get("/")
    assert "x-content-type-options" in response.headers
    assert "x-frame-options" in response.headers
    assert "x-xss-protection" in response.headers
    assert "strict-transport-security" in response.headers
