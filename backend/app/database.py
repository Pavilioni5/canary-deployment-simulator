"""
Database session and engine setup for SQLAlchemy.
Supports PostgreSQL (RDS/Docker) and SQLite fallback.
"""
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Adjust connection arguments if SQLite is used for local tests
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for obtaining database sessions per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all database tables registered with Base."""
    import app.models  # Ensure all models are registered with Base.metadata # noqa
    Base.metadata.create_all(bind=engine)


def check_db_tables():
    """Inspect and return existing table names."""
    inspector = inspect(engine)
    return inspector.get_table_names()
