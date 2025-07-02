from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
home, away = 0, 0          # score en mémoire

class Increment(BaseModel):
    team: str              # "home" ou "away"
    points: int            # 1, 2 ou 3

@app.post("/score/update")
def score_update(inc: Increment):
    global home, away
    if inc.team == "home":
        home += inc.points
    else:
        away += inc.points
    return {"home": home, "away": away}

@app.post("/score/update/reset")
def score_reset():
    global home, away
    home = away = 0
    return {"home": home, "away": away}
