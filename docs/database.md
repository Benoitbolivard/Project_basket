# Basketball Analytics Database

This document describes the database setup and usage for the Basketball Analytics platform.

## Phase 2: Backend & Database Implementation

The Phase 2 implementation adds PostgreSQL database persistence to the basketball analytics platform, replacing the previous in-memory cache system.

## Database Schema

The database consists of four main tables:

### `video_analyses`
Main table storing video analysis metadata and results.
- Primary key: UUID
- Contains video metadata (path, fps, dimensions, duration)
- Contains processing summary (frames processed, detection rates, etc.)
- Contains game statistics (total shots, possession changes, etc.)
- JSON fields for complex data structures

### `shot_attempts`
Individual shot attempt records linked to video analyses.
- Foreign key to `video_analyses`
- Shot metadata (timestamp, position, zone, confidence)
- Shot outcome (made/missed, point value)

### `possession_events`
Ball possession change events.
- Foreign key to `video_analyses`
- Event timing and player information
- Ball position data

### `player_stats`
Player performance statistics per analysis.
- Foreign key to `video_analyses`
- Comprehensive player metrics (shots, possessions, movement)

## Development Setup

### SQLite (Testing)
For development and testing, the system uses SQLite:

```bash
# Set testing mode
export TESTING=true

# Start development server
./scripts/start_api.sh
```

### PostgreSQL (Production)
For production deployment with PostgreSQL:

```bash
# Using Docker Compose
docker-compose up

# Or manually with PostgreSQL
export DATABASE_URL=postgresql://user:password@localhost:5432/basketball_analytics
poetry run alembic upgrade head
poetry run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

## Database Migrations

Database schema changes are managed with Alembic:

```bash
# Create a new migration
poetry run alembic revision --autogenerate -m "Description of changes"

# Apply migrations
poetry run alembic upgrade head

# Rollback migrations
poetry run alembic downgrade -1
```

## API Changes

The REST API maintains backward compatibility while now using persistent storage:

- All endpoints return the same data structures
- Analysis results are now stored permanently in the database
- Database health is included in the `/health` endpoint
- Analysis IDs are now UUIDs instead of simple strings

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (default: local PostgreSQL)
- `TESTING`: Set to "true" to use SQLite for testing (default: "false")

## Testing

Database functionality is tested with:

```bash
# Test database CRUD operations
poetry run python tests/test_database.py

# Test API with database integration
poetry run python tests/test_api_database.py

# Run all tests
poetry run python tests/test_basketball_vision.py
```