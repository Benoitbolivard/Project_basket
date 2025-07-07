from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health() -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() in ({"message": "Hello world"}, {"status": "ok"})
