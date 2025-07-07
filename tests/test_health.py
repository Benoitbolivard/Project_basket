from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() in ({"message": "Hello world"}, {"status": "ok"})
