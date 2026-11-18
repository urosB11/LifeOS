"""Tests for the /api/v1/health endpoint."""

def test_health_returns_ok(client):
    """Health endpoint returns 200 with status ok and database reachable."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "Life OS"
    assert data["database"] == "sqlite"


def test_health_rejects_unknown_host():
    """Requests with an unknown Host header are rejected (SECURITY.md)."""
    from app.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app, base_url="http://evil.example.com:8000")
    response = client.get("/api/v1/health", headers={"Host": "evil.example.com:8000"})
    assert response.status_code == 400