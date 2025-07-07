from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    teams = relationship("Team", back_populates="game")
    events = relationship("Event", back_populates="game")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    game_id = Column(Integer, ForeignKey("games.id"))

    game = relationship("Game", back_populates="teams")
    players = relationship("Player", back_populates="team")


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"))

    team = relationship("Team", back_populates="players")
    events = relationship("Event", back_populates="player")
    stats = relationship("StatsSnapshot", back_populates="player")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)
    timestamp = Column(DateTime)
    game_id = Column(Integer, ForeignKey("games.id"))
    player_id = Column(Integer, ForeignKey("players.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))

    game = relationship("Game", back_populates="events")
    player = relationship("Player", back_populates="events")
    team = relationship("Team")


class StatsSnapshot(Base):
    __tablename__ = "stats_snapshots"

    id = Column(Integer, primary_key=True)
    data = Column(String)
    game_id = Column(Integer, ForeignKey("games.id"))
    player_id = Column(Integer, ForeignKey("players.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))

    player = relationship("Player", back_populates="stats")
