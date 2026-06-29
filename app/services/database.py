"""
app/services/database.py
Database engine factory, session management, and table bootstrap.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from config.settings import DB_CONFIG
from app.models.transaction import Base, Transaction

logger = logging.getLogger(__name__)


class DatabaseService:
    """Singleton-style DB service; call .init() once at startup."""

    _engine = None
    _SessionLocal = None

    # ------------------------------------------------------------------ #
    #  Bootstrap                                                           #
    # ------------------------------------------------------------------ #
    @classmethod
    def init(cls) -> bool:
        """Create engine, ensure DB exists, create tables."""
        try:
            # Connect to server WITHOUT specifying the database first
            server_url = (
                f"mysql+pymysql://{DB_CONFIG.user}:{DB_CONFIG.password}"
                f"@{DB_CONFIG.host}:{DB_CONFIG.port}?charset=utf8mb4"
            )
            engine_tmp = create_engine(server_url, pool_pre_ping=True)
            with engine_tmp.connect() as conn:
                conn.execute(
                    text(
                        f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG.name}` "
                        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                    )
                )
                conn.commit()
            engine_tmp.dispose()

            # Now connect to the target DB
            cls._engine = create_engine(
                DB_CONFIG.url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                echo=False,
            )
            cls._SessionLocal = sessionmaker(bind=cls._engine, expire_on_commit=False)
            Base.metadata.create_all(cls._engine)
            logger.info("Database initialised successfully.")
            return True
        except Exception as exc:
            logger.error("DB init failed: %s", exc)
            return False

    # ------------------------------------------------------------------ #
    #  Session context manager                                            #
    # ------------------------------------------------------------------ #
    @classmethod
    @contextmanager
    def session(cls) -> Generator[Session, None, None]:
        if cls._SessionLocal is None:
            raise RuntimeError("DatabaseService not initialised. Call .init() first.")
        db: Session = cls._SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    #  Write helpers                                                       #
    # ------------------------------------------------------------------ #
    @classmethod
    def bulk_insert_transactions(cls, df: pd.DataFrame, session_id: str) -> int:
        """Insert cleaned DataFrame rows; returns count inserted."""
        records = []
        for _, row in df.iterrows():
            records.append(
                Transaction(
                    upload_session=session_id,
                    date=row["date"],
                    description=row["description"],
                    amount=row["amount"],
                    transaction_type=row["transaction_type"],
                    category=row["category"],
                    is_anomaly=bool(row.get("is_anomaly", False)),
                    anomaly_score=float(row.get("anomaly_score", 0.0)),
                )
            )
        with cls.session() as db:
            db.bulk_save_objects(records)
        return len(records)

    # ------------------------------------------------------------------ #
    #  Read helpers                                                        #
    # ------------------------------------------------------------------ #
    @classmethod
    def fetch_session_df(cls, session_id: str) -> pd.DataFrame:
        query = f"""
            SELECT id, date, description, amount, transaction_type,
                   category, is_anomaly, anomaly_score
            FROM transactions
            WHERE upload_session = '{session_id}'
            ORDER BY date
        """
        with cls._engine.connect() as conn:
            return pd.read_sql(text(query), conn)

    @classmethod
    def list_sessions(cls) -> list[str]:
        query = """
            SELECT DISTINCT upload_session, MIN(created_at) AS ts
            FROM transactions
            GROUP BY upload_session
            ORDER BY ts DESC
            LIMIT 20
        """
        with cls._engine.connect() as conn:
            result = conn.execute(text(query))
            return [row[0] for row in result.fetchall()]
