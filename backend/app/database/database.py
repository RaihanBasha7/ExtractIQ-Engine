from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def create_database():
    from app.database.models import RawTicket, ExtractionResult  # noqa: F401

    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT COUNT(*) FROM pragma_table_info('extraction_results') WHERE name='repair_attempts_json'")
        )
        if result.scalar() == 0:
            conn.execute(text("ALTER TABLE extraction_results ADD COLUMN repair_attempts_json TEXT"))
            conn.commit()
