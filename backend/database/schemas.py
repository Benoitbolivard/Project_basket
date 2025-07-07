from pydantic import BaseModel
from datetime import datetime


class GameSchema(BaseModel):
    id: int | None = None
    name: str

    class Config:
        orm_mode = True


class TeamSchema(BaseModel):
    id: int | None = None
    name: str
    game_id: int | None = None

    class Config:
        orm_mode = True


class PlayerSchema(BaseModel):
    id: int | None = None
    name: str
    team_id: int | None = None

    class Config:
        orm_mode = True


class EventSchema(BaseModel):
    id: int | None = None
    type: str
    timestamp: datetime | None = None
    game_id: int | None = None
    player_id: int | None = None
    team_id: int | None = None

    class Config:
        orm_mode = True


class StatsSnapshotSchema(BaseModel):
    id: int | None = None
    data: str | None = None
    game_id: int | None = None
    player_id: int | None = None
    team_id: int | None = None

    class Config:
        orm_mode = True


# Additional schemas used for the API
class GameOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class EventIn(BaseModel):
    type: str
    timestamp: datetime | None = None
    game_id: int
    player_id: int | None = None
    team_id: int | None = None


class StatsOut(BaseModel):
    id: int
    data: str | None = None
    game_id: int
    player_id: int | None = None
    team_id: int | None = None

    class Config:
        orm_mode = True
