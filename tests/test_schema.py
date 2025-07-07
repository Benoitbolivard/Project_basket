from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.models import Base, Game, Team, Player


def test_schema_creation_and_insertion():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        game = Game(name="Test Game")
        team = Team(name="Team A", game=game)
        player = Player(name="Player 1", team=team)
        session.add_all([game, team, player])
        session.commit()

        assert session.query(Game).count() == 1
        assert session.query(Team).count() == 1
        assert session.query(Player).count() == 1
