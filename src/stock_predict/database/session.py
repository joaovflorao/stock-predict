from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .config import settings


engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_connection() -> Generator[Session, None, None]:
    db_conn = SessionLocal()
    try:
        yield db_conn
    finally:
        db_conn.close()
