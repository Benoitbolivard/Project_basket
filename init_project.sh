#!/bin/bash
set -e

mkdir -p backend/app vision workers frontend tests docker

touch backend/app/__init__.py
cat <<'PY' > backend/app/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Hello world"}
PY

cat <<'DOCKER' > docker/Dockerfile.backend
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install poetry && poetry install --no-root
COPY backend ./backend
CMD ["poetry", "run", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
DOCKER

cat <<'GITIGNORE' > .gitignore
# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
*.egg-info/

# Virtualenv
venv/
.env/

# VSCode
.vscode/

# macOS
.DS_Store
GITIGNORE

cat <<'README' > README.md
# Project Basket

Monorepo pour l'analyse vidéo de basketball et l'API associée.
README

poetry init --name project_basket --python "^3.11" -n

cat <<'TOML' > pyproject.toml
[tool.poetry]
name = "project_basket"
version = "0.1.0"
description = ""
authors = []

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "*"
uvicorn = {extras = ["standard"], version = "*"}
pydantic = "*"
opencv-python = "*"
ultralytics = "*"

[tool.poetry.dev-dependencies]

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
TOML

