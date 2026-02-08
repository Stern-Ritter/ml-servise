from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
from .config import get_settings


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
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(drop_all: bool = False) -> None:
    try:
        from models.base import Base
        from models.user import User, Role
        from models.finance import Balance, Transaction
        from models.predict import Patient, PredictTask, Predict

        if drop_all:
            Base.metadata.drop_all(engine)

        Base.metadata.create_all(engine)
    except Exception as e:
        raise
