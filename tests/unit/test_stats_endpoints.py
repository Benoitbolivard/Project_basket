"""Test the new stats endpoints."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.app.main import app
from backend.app.database import get_db, SessionLocal
from backend.app import crud, db_models
from fastapi.testclient import TestClient
import pytest
from datetime import datetime


def get_test_db():
    """Override database dependency for testing."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = get_test_db
client = TestClient(app)


def setup_test_data(db):
    """Set up test data for stats endpoints."""
    # Create test clubs
    club1 = crud.create_club(db, "Lakers", "LAL", "Los Angeles")
    club2 = crud.create_club(db, "Warriors", "GSW", "San Francisco")
    
    # Create test players
    player1 = crud.create_player(db, club1.id, "LeBron James", 23, "SF")
    player2 = crud.create_player(db, club1.id, "Anthony Davis", 3, "PF")
    player3 = crud.create_player(db, club2.id, "Stephen Curry", 30, "PG")
    
    # Create test match
    match = crud.create_match(
        db, 
        club1.id, 
        club2.id, 
        datetime(2024, 1, 15, 19, 30)
    )
    
    # Create test stats
    stats_data_lebron = {
        'minutes_played': 36.5,
        'points': 28,
        'field_goals_made': 10,
        'field_goals_attempted': 18,
        'three_points_made': 2,
        'three_points_attempted': 6,
        'distance_covered_m': 2840.5,
        'avg_speed_kmh': 12.8,
        'max_speed_kmh': 24.5,
        'ball_touches': 89
    }
    
    stats_data_curry = {
        'minutes_played': 35.2,
        'points': 32,
        'field_goals_made': 11,
        'field_goals_attempted': 20,
        'three_points_made': 6,
        'three_points_attempted': 12,
        'distance_covered_m': 2720.1,
        'avg_speed_kmh': 11.9,
        'max_speed_kmh': 23.1,
        'ball_touches': 156
    }
    
    crud.create_or_update_player_stats(db, match.id, player1.id, stats_data_lebron)
    crud.create_or_update_player_stats(db, match.id, player3.id, stats_data_curry)
    
    return {
        'clubs': [club1, club2],
        'players': [player1, player2, player3],
        'match': match
    }


def test_player_stats_endpoint():
    """Test GET /players/{id}/stats endpoint."""
    db = SessionLocal()
    try:
        # Setup test data
        test_data = setup_test_data(db)
        player = test_data['players'][0]  # LeBron James
        match = test_data['match']
        
        # Test getting player stats for specific match
        response = client.get(f"/players/{player.id}/stats?match_id={match.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data['player_id'] == player.id
        assert data['player_name'] == "LeBron James"
        assert data['games_played'] == 1
        assert data['total_points'] == 28
        assert data['total_distance_covered_m'] == 2840.5
        assert 'match_stats' in data
        
        # Test getting all player stats
        response = client.get(f"/players/{player.id}/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data['player_id'] == player.id
        assert data['games_played'] == 1
        
        # Test non-existent player
        response = client.get("/players/99999/stats")
        assert response.status_code == 404
        
    finally:
        # Cleanup
        db.query(db_models.StatPublic).delete()
        db.query(db_models.Match).delete()
        db.query(db_models.ClubPlayer).delete()
        db.query(db_models.Club).delete()
        db.commit()
        db.close()


def test_match_stats_endpoint():
    """Test GET /matches/{id}/stats endpoint."""
    db = SessionLocal()
    try:
        # Setup test data
        test_data = setup_test_data(db)
        match = test_data['match']
        
        # Test getting match stats
        response = client.get(f"/matches/{match.id}/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data['match_id'] == match.id
        assert 'home_team' in data
        assert 'away_team' in data
        assert data['home_team']['team_name'] == "Lakers"
        assert data['away_team']['team_name'] == "Warriors"
        
        # Check team stats
        assert data['home_team']['total_points'] == 28  # LeBron's points
        assert data['away_team']['total_points'] == 32  # Curry's points
        
        # Check player lists
        assert len(data['home_team']['players']) == 1
        assert len(data['away_team']['players']) == 1
        
        # Test non-existent match
        response = client.get("/matches/99999/stats")
        assert response.status_code == 404
        
    finally:
        # Cleanup
        db.query(db_models.StatPublic).delete()
        db.query(db_models.Match).delete()
        db.query(db_models.ClubPlayer).delete()
        db.query(db_models.Club).delete()
        db.commit()
        db.close()


def test_job_status_endpoint():
    """Test GET /jobs/{id} endpoint."""
    # Test with non-existent job (Redis not available in test)
    response = client.get("/jobs/test-job-id")
    assert response.status_code == 503  # Service unavailable when Redis not connected


def test_upload_endpoint_validation():
    """Test upload endpoint validation."""
    # Test upload without file
    response = client.post("/upload")
    assert response.status_code == 422  # Validation error
    
    # Test upload with invalid file type would require actual file upload
    # This is more of an integration test


if __name__ == "__main__":
    # Run tests manually
    print("Running stats endpoint tests...")
    test_player_stats_endpoint()
    print("✅ Player stats endpoint test passed")
    
    test_match_stats_endpoint()
    print("✅ Match stats endpoint test passed")
    
    test_job_status_endpoint()
    print("✅ Job status endpoint test passed")
    
    test_upload_endpoint_validation()
    print("✅ Upload validation test passed")
    
    print("All tests passed!")