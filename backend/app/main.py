from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def read_root():
    return {"message": "Hello world"}


@app.get("/healthy")
async def healthy() -> dict[str, str]:
    return {"status": "ok"}
