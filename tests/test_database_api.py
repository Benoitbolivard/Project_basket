"""Test database integration and API endpoints."""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import get_db, Base
from backend.app import crud


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    """Setup clean database for each test."""
    # Drop all tables and recreate
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup after test
    Base.metadata.drop_all(bind=engine)


class TestDatabaseIntegration:
    """Test database operations."""

    def test_create_analysis(self, setup_database):
        """Test creating an analysis record."""
        db = TestingSessionLocal()
        
        analysis_id = f"test-analysis-{uuid.uuid4()}"
        analysis = crud.create_analysis(
            db, 
            analysis_id, 
            "/path/to/video.mp4",
            confidence_threshold=0.3
        )
        
        assert analysis.id == analysis_id
        assert analysis.video_path == "/path/to/video.mp4"
        assert analysis.confidence_threshold == 0.3
        assert analysis.status == "processing"
        
        db.close()

    def test_get_analysis(self, setup_database):
        """Test retrieving an analysis."""
        db = TestingSessionLocal()
        
        analysis_id = f"test-get-{uuid.uuid4()}"
        
        # Create analysis
        crud.create_analysis(db, analysis_id, "/path/to/video.mp4")
        
        # Retrieve analysis
        analysis = crud.get_analysis(db, analysis_id)
        assert analysis is not None
        assert analysis.id == analysis_id
        
        # Test non-existent analysis
        non_existent = crud.get_analysis(db, "does-not-exist")
        assert non_existent is None
        
        db.close()

    def test_delete_analysis(self, setup_database):
        """Test deleting an analysis."""
        db = TestingSessionLocal()
        
        analysis_id = f"test-delete-{uuid.uuid4()}"
        
        # Create analysis
        crud.create_analysis(db, analysis_id, "/path/to/video.mp4")
        
        # Verify it exists
        analysis = crud.get_analysis(db, analysis_id)
        assert analysis is not None
        
        # Delete it
        result = crud.delete_analysis(db, analysis_id)
        assert result is True
        
        # Verify it's gone
        analysis = crud.get_analysis(db, analysis_id)
        assert analysis is None
        
        db.close()


class TestAPIEndpoints:
    """Test API endpoints."""

    def test_health_check(self, setup_database):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_list_analyses_empty(self, setup_database):
        """Test listing analyses when none exist."""
        response = client.get("/analyze")
        assert response.status_code == 200
        data = response.json()
        assert "analyses" in data
        assert "total_count" in data
        assert isinstance(data["analyses"], list)

    def test_get_nonexistent_analysis(self, setup_database):
        """Test getting a non-existent analysis."""
        response = client.get("/analyze/does-not-exist")
        assert response.status_code == 404

    def test_shot_chart_nonexistent_analysis(self, setup_database):
        """Test shot chart for non-existent analysis."""
        response = client.get("/analyze/does-not-exist/shot-chart")
        assert response.status_code == 404

    def test_live_data_nonexistent_analysis(self, setup_database):
        """Test live data for non-existent analysis."""
        response = client.get("/analyze/does-not-exist/live-data")
        assert response.status_code == 404

    def test_delete_nonexistent_analysis(self, setup_database):
        """Test deleting a non-existent analysis."""
        response = client.delete("/analyze/does-not-exist")
        assert response.status_code == 404


class TestFrontend:
    """Test frontend accessibility."""

    def test_dashboard_accessible(self, setup_database):
        """Test that dashboard is accessible."""
        response = client.get("/dashboard/")
        assert response.status_code == 200
        assert "Basketball Analytics Dashboard" in response.text

    def test_root_redirects_to_dashboard(self, setup_database):
        """Test that root redirects to dashboard."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 302 or response.status_code == 307


if __name__ == "__main__":
    pytest.main([__file__, "-v"])