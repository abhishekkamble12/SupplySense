import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
try:
    from db.models import Base
    from constants import DATABASE_URL_KEY, DEFAULT_DATABASE_URL
except ImportError:
    from src.db.models import Base
    from src.constants import DATABASE_URL_KEY, DEFAULT_DATABASE_URL


def get_database_url() -> str:
    url = os.getenv(DATABASE_URL_KEY, DEFAULT_DATABASE_URL)
    # Fix postgres:// legacy URLs if present in cloud envs (e.g. Heroku / Render)
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url

DATABASE_URL = get_database_url()

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initializes relational database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """FastAPI Dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
