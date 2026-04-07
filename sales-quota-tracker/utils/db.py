"""Database setup for the Sales Quota Tracker.

Uses SQLAlchemy ORM with a local SQLite database.
"""

from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"

# SQLite in-file database
ENGINE = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False)
Base = declarative_base()


def init_db():
    """Create database tables and apply migrations."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=ENGINE)
    
    # Apply migrations for existing databases
    _apply_migrations()


def _apply_migrations():
    """Apply database migrations for schema updates."""
    with SessionLocal() as session:
        # Migration: Add is_excluded column to client_master if it doesn't exist
        try:
            session.execute(
                text("SELECT is_excluded FROM client_master LIMIT 1")
            )
        except Exception:
            # Column doesn't exist, add it
            try:
                session.execute(
                    text("ALTER TABLE client_master ADD COLUMN is_excluded INTEGER DEFAULT 0")
                )
                session.commit()
            except Exception:
                # Column may already exist or table doesn't exist, that's okay
                pass
