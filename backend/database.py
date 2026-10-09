"""DB engine/session. SQLite by default, Postgres via DATABASE_URL."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .env import load as _load_env

_load_env()

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./retainiq.db")
# Render/Heroku-style Postgres URLs use the bare `postgres://` scheme, which
# SQLAlchemy rejects. Normalize to an explicit psycopg2 URL.
if DB_URL.startswith("postgres://"):
    DB_URL = "postgresql+psycopg2://" + DB_URL[len("postgres://"):]
elif DB_URL.startswith("postgresql://"):
    DB_URL = "postgresql+psycopg2://" + DB_URL[len("postgresql://"):]
connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
engine = create_engine(DB_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
