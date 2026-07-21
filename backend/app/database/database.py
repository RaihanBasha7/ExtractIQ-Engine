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
        for col, col_type in [
            ("repair_attempts_json", "TEXT"),
            ("confidence_score", "FLOAT"),
            ("validation_status", "VARCHAR(20)"),
            ("repair_attempts_count", "INTEGER"),
            ("final_status", "VARCHAR(20)"),
            ("needs_review_reason", "TEXT"),
        ]:
            result = conn.execute(
                text(f"SELECT COUNT(*) FROM pragma_table_info('extraction_results') WHERE name='{col}'")
            )
            if result.scalar() == 0:
                conn.execute(text(f"ALTER TABLE extraction_results ADD COLUMN {col} {col_type}"))
        conn.commit()
