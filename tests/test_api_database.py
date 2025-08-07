"""Test API with database integration."""

import os
import sys
from pathlib import Path

# Set testing mode before importing anything
os.environ["TESTING"] = "true"

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import create_tables, drop_tables


# Create test client
client = TestClient(app)


def test_api_endpoints():
    """Test API endpoints with database integration."""
    print("Testing API endpoints with database...")
    
    # Create tables
    create_tables()
    
    # Test health check
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database_status" in data
    print("✓ Health check endpoint working")
    
    # Test root endpoint
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Basketball Analytics API" in data["message"]
    print("✓ Root endpoint working")
    
    # Test list analyses (should be empty initially)
    response = client.get("/analyze")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 0
    assert data["analyses"] == []
    print("✓ List analyses endpoint working")
    
    # Test getting non-existent analysis
    response = client.get("/analyze/non-existent-id")
    assert response.status_code == 404
    print("✓ 404 for non-existent analysis")
    
    # Test deleting non-existent analysis
    response = client.delete("/analyze/non-existent-id")
    assert response.status_code == 404
    print("✓ 404 for deleting non-existent analysis")
    
    print("All API endpoint tests passed! ✅")


if __name__ == "__main__":
    test_api_endpoints()