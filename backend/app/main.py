from fastapi import FastAPI

from .api import router

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Hello world"}

app.include_router(router)
