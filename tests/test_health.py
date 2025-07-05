from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_root_health() -> None:
    """Vérifie que la route racine répond 200 et le JSON attendu."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello world"}
