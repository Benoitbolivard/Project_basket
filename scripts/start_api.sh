#!/bin/bash

# Start the Basketball Analytics API server

echo "🏀 Starting Basketball Analytics API server..."

# Set testing mode for development (uses SQLite)
export TESTING=true

# Create database tables
echo "📊 Creating database tables..."
poetry run python -c "from backend.app.database import create_tables; create_tables()"

# Start the server
echo "🚀 Starting FastAPI server on http://localhost:8000"
poetry run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload