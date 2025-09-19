from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import Column, Float, Integer, MetaData, String, Table, create_engine, text
from sqlalchemy.engine import Engine

# Simple SQLite setup with a single media table and a minimal migration to v1.
# DB path: env SKYLAPSE_DB or <storage.local_dir>/media.sqlite3 (provided by caller)

metadata = MetaData()

media_table = Table(
    "media",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("path", String, nullable=False),
    Column("url", String, nullable=False),
    Column("captured_at", Float, nullable=False),  # unix timestamp
    Column("size_bytes", Integer, nullable=False),
    Column("width", Integer, nullable=False),
    Column("height", Integer, nullable=False),
    Column("exposure_us", Integer, nullable=True),
)

schema_version_table = Table(
    "schema_version",
    metadata,
    Column("version", Integer, primary_key=True),
)


@dataclass
class MediaRow:
    id: int
    path: str
    url: str
    captured_at: float
    size_bytes: int
    width: int
    height: int
    exposure_us: int | None


def get_engine(db_path: Path) -> Engine:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}", future=True)


def _get_db_path(storage_dir: Path) -> Path:
    # Allow override with environment variable
    override = os.getenv("SKYLAPSE_DB")
    if override:
        return Path(override)
    return storage_dir / "media.sqlite3"


def init_db(storage_dir: Path) -> Path:
    """Create DB and tables if not exist; record schema version (v1)."""
    db_path = _get_db_path(storage_dir)
    engine = get_engine(db_path)
    with engine.begin() as conn:
        # Create tables if not exist
        metadata.create_all(conn)
        # Initialize schema version if empty
        cur = None
        if engine.dialect.has_table(conn, "schema_version"):
            cur = conn.execute(text("SELECT COUNT(1) FROM schema_version"))
        try:
            count = cur.scalar_one() if cur is not None else 0
        except Exception:
            count = 0
        if not count:
            conn.execute(schema_version_table.insert().values(version=1))
    return db_path


def insert_media(
    storage_dir: Path,
    *,
    path: Path,
    url: str,
    captured_at: float,
    size_bytes: int,
    width: int,
    height: int,
    exposure_us: int | None,
) -> None:
    db_path = init_db(storage_dir)
    engine = get_engine(db_path)
    with engine.begin() as conn:
        conn.execute(
            media_table.insert().values(
                path=str(path),
                url=url,
                captured_at=captured_at,
                size_bytes=size_bytes,
                width=width,
                height=height,
                exposure_us=exposure_us,
            )
        )


def list_media(
    storage_dir: Path,
    *,
    from_ts: float | None = None,
    to_ts: float | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    db_path = init_db(storage_dir)
    engine = get_engine(db_path)
    offset = max(0, (page - 1) * page_size)

    where = []
    params: dict[str, Any] = {}
    if from_ts is not None:
        where.append("captured_at >= :from_ts")
        params["from_ts"] = from_ts
    if to_ts is not None:
        where.append("captured_at <= :to_ts")
        params["to_ts"] = to_ts

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    with engine.begin() as conn:
        total = conn.execute(text(f"SELECT COUNT(1) FROM media {where_sql}"), params).scalar_one()
        rows = (
            conn.execute(
                text(
                    f"SELECT id, path, url, captured_at, size_bytes, width, height, exposure_us "
                    f"FROM media {where_sql} ORDER BY captured_at DESC LIMIT :limit OFFSET :offset"
                ),
                {**params, "limit": page_size, "offset": offset},
            )
            .mappings()
            .all()
        )

    return {
        "page": page,
        "page_size": page_size,
        "total": int(total),
        "items": [dict(r) for r in rows],
    }
