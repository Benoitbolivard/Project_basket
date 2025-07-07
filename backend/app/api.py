from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.database.models import Game, Event, StatsSnapshot
from backend.database.schemas import GameOut, EventIn, StatsOut

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/games", response_model=list[GameOut])
def list_games(db: Session = Depends(get_db)):
    return db.query(Game).all()


@router.get("/games/{game_id}", response_model=GameOut)
def get_game(game_id: int, db: Session = Depends(get_db)):
    game = db.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.post("/events", status_code=201)
def create_event(event: EventIn, db: Session = Depends(get_db)):
    db_event = Event(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return {"id": db_event.id}


@router.get("/stats/{game_id}", response_model=list[StatsOut])
def get_stats(game_id: int, db: Session = Depends(get_db)):
    return db.query(StatsSnapshot).filter(StatsSnapshot.game_id == game_id).all()
