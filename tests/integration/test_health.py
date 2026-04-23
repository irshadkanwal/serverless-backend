from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.app_factory import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    @patch("app.services.db.file_db_service.FileDatabaseService.get_connection")
    def test_health_check_success(self, mock_get_connection, client):
        # Mock successful database connection
        mock_connection = AsyncMock()
        mock_connection.fetchval.return_value = 1
        mock_get_connection.return_value.__aenter__.return_value = mock_connection
        mock_get_connection.return_value.__aexit__.return_value = None

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    @patch("app.services.db.file_db_service.FileDatabaseService.get_connection")
    def test_health_check_database_failure(self, mock_get_connection, client):
        # Mock database connection failure
        mock_get_connection.side_effect = Exception("Database connection failed")

        response = client.get("/health")

        assert response.status_code == 503
        data = response.json()
        assert "status" in data["detail"]
        assert data["detail"]["status"] == "unhealthy"
