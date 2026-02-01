"""Tests for main application endpoints."""


def test_root_endpoint(client):
    """Test the root endpoint returns API info."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["status"] == "running"


def test_health_endpoint(client):
    """Test the basic health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_liveness_endpoint(client):
    """Test the liveness probe endpoint."""
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_endpoint_db_down(client, mock_db):
    """Test readiness check when database is unavailable."""
    mock_db.execute.side_effect = Exception("Connection refused")

    response = client.get("/health/ready")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unhealthy"
    assert "database" in data["checks"]
    assert "unhealthy" in data["checks"]["database"]


def test_readiness_endpoint_db_up(client, mock_db):
    """Test readiness check when database is available."""
    mock_db.execute.return_value = [{"ping": 1}]

    response = client.get("/health/ready")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["checks"]["database"] == "healthy"


def test_cors_headers(client):
    """Test CORS headers are present."""
    response = client.options(
        "/",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "GET"
        }
    )

    assert "access-control-allow-origin" in response.headers
