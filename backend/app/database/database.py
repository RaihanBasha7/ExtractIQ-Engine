from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATABASE_URL
from app.logging import get_logger

logger = get_logger(__name__)

_engine = None
_SessionLocal = None


def _get_engine():
    global _engine
    if _engine is None:
        connect_args = {}
        url = DATABASE_URL
        if url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        _engine = create_engine(url, echo=False, connect_args=connect_args)
        logger.info("Database engine created: %s", url.split("://")[0])
    return _engine


def _get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_get_engine())
    return _SessionLocal


engine = _get_engine()
SessionLocal = _get_session_local()


class Base(DeclarativeBase):
    pass


def create_database():
    from app.database.models import ExtractionResult, RawTicket  # noqa: F401

    Base.metadata.create_all(bind=engine)

    if engine.dialect.name == "sqlite":
        _migrate_sqlite()


def _migrate_sqlite():
    with engine.connect() as conn:
        existing = set(
            row[0]
            for row in conn.execute(
                text("SELECT name FROM pragma_table_info('extraction_results')")
            ).fetchall()
        )
        migrations = [
            ("repair_attempts_json", "TEXT"),
            ("confidence_score", "FLOAT"),
            ("validation_status", "VARCHAR(20)"),
            ("repair_attempts_count", "INTEGER"),
            ("final_status", "VARCHAR(20)"),
            ("needs_review_reason", "TEXT"),
        ]
        for col, col_type in migrations:
            if col not in existing:
                conn.execute(text(f"ALTER TABLE extraction_results ADD COLUMN {col} {col_type}"))
        conn.commit()
