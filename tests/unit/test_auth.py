"""Test authentication endpoints and JWT functionality."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.app.main import app
from backend.app.database import get_db, SessionLocal
from backend.app import crud, db_models
from backend.app.auth import hash_password, verify_password, create_access_token, decode_access_token
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


def test_password_hashing():
    """Test password hashing and verification."""
    password = "test_password_123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong_password", hashed)


def test_jwt_token_creation_and_decoding():
    """Test JWT token creation and decoding."""
    data = {"sub": "testuser", "role": "club", "user_id": 1}
    token = create_access_token(data)
    
    assert token is not None
    
    decoded = decode_access_token(token)
    assert decoded["sub"] == "testuser"
    assert decoded["role"] == "club"
    assert decoded["user_id"] == 1


def test_user_registration():
    """Test user registration endpoint."""
    db = SessionLocal()
    try:
        # Clean up any existing test user
        existing_user = crud.get_user_by_username(db, "testuser")
        if existing_user:
            db.delete(existing_user)
            db.commit()
        
        # Test registration
        response = client.post("/auth/register", data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "role": "club"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["role"] == "club"
        
        # Test duplicate username
        response = client.post("/auth/register", data={
            "username": "testuser",
            "email": "test2@example.com",
            "password": "testpass123",
            "role": "public"
        })
        
        assert response.status_code == 400
        assert "already taken" in response.json()["detail"]
        
    finally:
        # Cleanup
        test_user = crud.get_user_by_username(db, "testuser")
        if test_user:
            db.delete(test_user)
            db.commit()
        db.close()


def test_user_login():
    """Test user login endpoint."""
    db = SessionLocal()
    try:
        # Create test user
        hashed_password = hash_password("testpass123")
        test_user = crud.create_user(
            db, 
            email="test@example.com",
            username="testuser",
            hashed_password=hashed_password,
            role="club"
        )
        
        # Test successful login
        response = client.post("/auth/login", data={
            "username": "testuser",
            "password": "testpass123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "testuser"
        assert data["user"]["role"] == "club"
        
        # Test wrong password
        response = client.post("/auth/login", data={
            "username": "testuser",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        
        # Test non-existent user
        response = client.post("/auth/login", data={
            "username": "nonexistent",
            "password": "testpass123"
        })
        
        assert response.status_code == 401
        
    finally:
        # Cleanup
        if test_user:
            db.delete(test_user)
            db.commit()
        db.close()


def test_protected_endpoint():
    """Test protected club endpoint access."""
    db = SessionLocal()
    try:
        # Create test user and club
        test_club = crud.create_club(db, "Test Club", "TEST", "Test City")
        hashed_password = hash_password("testpass123")
        test_user = crud.create_user(
            db,
            email="test@example.com",
            username="testuser",
            hashed_password=hashed_password,
            role="club",
            club_id=test_club.id
        )
        
        # Get access token
        login_response = client.post("/auth/login", data={
            "username": "testuser",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]
        
        # Test protected endpoint with valid token
        response = client.get("/club/dashboard-data", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["club"]["name"] == "Test Club"
        
        # Test protected endpoint without token
        response = client.get("/club/dashboard-data")
        assert response.status_code == 403  # No authorization header
        
        # Test protected endpoint with invalid token
        response = client.get("/club/dashboard-data", headers={
            "Authorization": "Bearer invalid_token"
        })
        assert response.status_code == 401
        
    finally:
        # Cleanup
        if test_user:
            db.delete(test_user)
        if test_club:
            db.delete(test_club)
        db.commit()
        db.close()


if __name__ == "__main__":
    # Run tests manually
    print("Running authentication tests...")
    
    test_password_hashing()
    print("✅ Password hashing test passed")
    
    test_jwt_token_creation_and_decoding()
    print("✅ JWT token test passed")
    
    test_user_registration()
    print("✅ User registration test passed")
    
    test_user_login()
    print("✅ User login test passed")
    
    test_protected_endpoint()
    print("✅ Protected endpoint test passed")
    
    print("All authentication tests passed!")