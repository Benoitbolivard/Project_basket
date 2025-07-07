from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app import api as api_module
from backend.database.models import Base, Game, Team, Player


# Setup in-memory database for testing
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[api_module.get_db] = override_get_db
client = TestClient(app)


# Insert initial data
with TestingSessionLocal() as session:
    game = Game(name="Test Game")
    team = Team(name="Team A", game=game)
    player = Player(name="Player 1", team=team)
    session.add_all([game, team, player])
    session.commit()


def test_get_games():
    response = client.get("/games")
    assert response.status_code == 200
    assert response.json() == [{"id": 1, "name": "Test Game"}]


def test_post_events():
    data = {"type": "score", "game_id": 1}
    response = client.post("/events", json=data)
    assert response.status_code == 201
