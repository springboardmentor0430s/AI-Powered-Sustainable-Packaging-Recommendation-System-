from __future__ import annotations

import os
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

"""
Database configuration module.

This module creates a SQLAlchemy engine and session factory based on the
environment.  In development and testing, if no DATABASE_URL is provided,
the application will fall back to a local SQLite database.  When targeting
PostgreSQL, set the DATABASE_URL environment variable accordingly.
We also handle SQLite's `check_same_thread` option and ensure that the
engine uses `pool_pre_ping` for reliability.
"""
# Determine the database URL.  Prefer the DATABASE_URL environment variable
# which may point to a PostgreSQL instance.  If absent, build a URL from
# individual components (DB_USER, DB_PASS, etc.), and finally fall back to
# SQLite for local development.  The use of `quote_plus` ensures special
# characters in passwords are encoded correctly.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")
    # If all Postgres components are provided, construct a Postgres URL.
    if DB_USER and DB_HOST and DB_NAME:
        DB_PASS_Q = quote_plus(DB_PASS or "")
        host_part = f"{DB_HOST}:{DB_PORT or '5432'}"
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS_Q}@{host_part}/{DB_NAME}"
    else:
        # Default to a local SQLite database.  This is useful for local
        # development, unit tests, or environments without Postgres.  The
        # database file will be created in the project root if it does not exist.  
        DATABASE_URL = "sqlite:///./ecopackai.db"


def _create_engine(db_url: str) -> Engine:
    """Create a SQLAlchemy engine with sensible defaults based on the URL."""
    if db_url.startswith("sqlite"):
        # SQLite requires check_same_thread=False when used with FastAPI/async
        return create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
            future=True,
        )
    return create_engine(
        db_url,
        pool_pre_ping=True,
        future=True,
    )


# Initialise the engine and session factory.  The Engine is created once
# at import time.  If you change DATABASE_URL at runtime (not recommended),
# you should recreate the engine accordingly.
engine: Engine = _create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()


def get_db():
    """
    Provide a transactional scope around a series of operations.  When used
    as a FastAPI dependency, this yields a database session and ensures it is
    closed after the request is processed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
