from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from config import get_settings
from seed import seed_database


def get_database_engine():
    settings = get_settings()

    engine = create_engine(
        url=settings.DATABASE_URL_psycopg,
        echo=settings.DEBUG,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    return engine


engine = get_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db(drop_all: bool = False) -> None:
    try:
        from models.base import Base
        from models.user import User, Role
        from models.finance import Balance, Transaction
        from models.predict import Patient, PredictTask, Predict

        if drop_all:
            Base.metadata.drop_all(engine)

        Base.metadata.create_all(engine)
        seed_database()
    except Exception as e:
        raise


def health_check_db() -> str:
    try:
        session = SessionLocal()
        try:
            session.execute(text("SELECT 1"))
            return "connected"
        finally:
            session.close()
    except Exception as e:
        return f"disconnected: {e}"
