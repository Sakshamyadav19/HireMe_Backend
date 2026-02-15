from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config.settings import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,   # Test connections before use; discard if closed (e.g. Neon idle timeout)
    pool_recycle=300,     # Recycle connections after 5 min so they don't exceed server idle timeout
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
