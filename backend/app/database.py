"""Database configuration and connection management."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Database URL from environment variable or default to SQLite for development
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://basketball_user:basketball_pass@localhost/basketball_db"
)

# For development, fall back to SQLite if PostgreSQL is not available
SQLITE_DATABASE_URL = "sqlite:///./basketball.db"

try:
    # Try PostgreSQL first
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
    )
    # Test connection
    with engine.connect() as conn:
        conn.execute("SELECT 1")
    print("Connected to PostgreSQL database")
except Exception as e:
    print(f"PostgreSQL connection failed: {e}")
    print("Falling back to SQLite for development")
    engine = create_engine(
        SQLITE_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)