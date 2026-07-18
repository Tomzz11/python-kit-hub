#!/usr/bin/env python3
# ============================================================
# DB HELPER — Utility Scripts
# ============================================================
"""
Database utility สำหรับ SQLite (ใช้ stdlib):
  - DatabaseManager : connection pool + context manager
  - QueryBuilder    : type-safe query builder
  - Migration       : schema versioning
  - Repository      : generic CRUD

สำหรับ PostgreSQL/MySQL: แทนที่ sqlite3 ด้วย psycopg2 / mysql-connector
"""

import sqlite3
import json
import logging
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, TypeVar, Generic
from dataclasses import dataclass, asdict, fields

T = TypeVar("T")
Record = dict[str, Any]

logger = logging.getLogger(__name__)

# ── 1. DatabaseManager ───────────────────────────────────────
class DatabaseManager:
    """
    SQLite connection manager พร้อม:
    - auto-commit / rollback
    - row_factory → dict
    - WAL mode (concurrent reads)
    """

    def __init__(self, db_path: str | Path = ":memory:"):
        self.db_path = str(db_path)
        self._conn: sqlite3.Connection | None = None

    def connect(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row   # dict-like rows
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self): return self.connect()
    def __exit__(self, *_): self.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Auto-commit or rollback context"""
        conn = self._conn or self.connect()._conn
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        with self.transaction() as conn:
            cur = conn.execute(sql, params)
            return cur

    def executemany(self, sql: str, params_seq: list) -> sqlite3.Cursor:
        with self.transaction() as conn:
            return conn.executemany(sql, params_seq)

    def query(self, sql: str, params: tuple | dict = ()) -> list[dict]:
        conn = self._conn or self.connect()._conn
        cur  = conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]

    def query_one(self, sql: str, params: tuple | dict = ()) -> dict | None:
        rows = self.query(sql, params)
        return rows[0] if rows else None

# ── 2. QueryBuilder ──────────────────────────────────────────
class QueryBuilder:
    """
    Fluent query builder — ป้องกัน SQL injection

    Usage:
        q = (QueryBuilder("users")
             .select("id", "name", "email")
             .where("age > ?", 18)
             .where("active = ?", 1)
             .order_by("name")
             .limit(10))
        sql, params = q.build()
    """

    def __init__(self, table: str):
        self._table   = table
        self._select  = ["*"]
        self._wheres: list[tuple[str, Any]] = []
        self._order:  list[str] = []
        self._limit:  int | None = None
        self._offset: int | None = None
        self._joins:  list[str]  = []

    def select(self, *cols: str)              -> "QueryBuilder": self._select = list(cols); return self
    def where(self, cond: str, *vals)         -> "QueryBuilder": self._wheres.append((cond, vals)); return self
    def order_by(self, *cols: str)            -> "QueryBuilder": self._order = list(cols); return self
    def limit(self, n: int)                   -> "QueryBuilder": self._limit  = n; return self
    def offset(self, n: int)                  -> "QueryBuilder": self._offset = n; return self
    def join(self, clause: str)               -> "QueryBuilder": self._joins.append(clause); return self

    def build(self) -> tuple[str, tuple]:
        cols   = ", ".join(self._select)
        sql    = f"SELECT {cols} FROM {self._table}"
        params = []

        for join in self._joins:
            sql += f" {join}"

        if self._wheres:
            parts   = [w[0] for w in self._wheres]
            sql    += " WHERE " + " AND ".join(parts)
            for _, vals in self._wheres:
                params.extend(vals)

        if self._order:
            sql += " ORDER BY " + ", ".join(self._order)

        if self._limit is not None:
            sql += f" LIMIT {self._limit}"

        if self._offset is not None:
            sql += f" OFFSET {self._offset}"

        return sql, tuple(params)

    def run(self, db: DatabaseManager) -> list[dict]:
        sql, params = self.build()
        return db.query(sql, params)

# ── 3. Migration ─────────────────────────────────────────────
class Migration:
    """Simple schema version management"""

    def __init__(self, db: DatabaseManager):
        self._db = db
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                version   INTEGER PRIMARY KEY,
                name      TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
        """)

    def apply(self, version: int, name: str, sql: str):
        exists = self._db.query_one(
            "SELECT 1 FROM _migrations WHERE version = ?", (version,))
        if exists:
            return
        logger.info(f"Applying migration {version}: {name}")
        self._db.execute(sql)
        self._db.execute(
            "INSERT INTO _migrations (version, name, applied_at) VALUES (?,?,?)",
            (version, name, datetime.utcnow().isoformat())
        )

    def current_version(self) -> int:
        row = self._db.query_one("SELECT MAX(version) AS v FROM _migrations")
        return row["v"] or 0 if row else 0

# ── 4. Repository (Generic CRUD) ─────────────────────────────
class Repository(Generic[T]):
    """
    Generic CRUD repository

    Usage:
        class User:
            id: int; name: str; email: str

        repo = Repository(db, "users", User)
        repo.insert({"name": "Alice", "email": "alice@example.com"})
        users = repo.find(where="name LIKE ?", params=("%Alice%",))
    """

    def __init__(self, db: DatabaseManager, table: str, model_cls: type | None = None):
        self._db    = db
        self._table = table
        self._model = model_cls

    def insert(self, data: Record) -> int:
        cols     = ", ".join(data.keys())
        placeholders = ", ".join("?" * len(data))
        sql      = f"INSERT INTO {self._table} ({cols}) VALUES ({placeholders})"
        cur      = self._db.execute(sql, tuple(data.values()))
        return cur.lastrowid or 0

    def insert_many(self, records: list[Record]):
        if not records:
            return
        cols         = ", ".join(records[0].keys())
        placeholders = ", ".join("?" * len(records[0]))
        sql          = f"INSERT INTO {self._table} ({cols}) VALUES ({placeholders})"
        self._db.executemany(sql, [tuple(r.values()) for r in records])

    def find(
        self,
        where: str | None = None,
        params: tuple = (),
        order_by: str | None = None,
        limit: int | None = None,
    ) -> list[Record]:
        sql = f"SELECT * FROM {self._table}"
        if where:
            sql += f" WHERE {where}"
        if order_by:
            sql += f" ORDER BY {order_by}"
        if limit is not None:
            sql += f" LIMIT {limit}"
        return self._db.query(sql, params)

    def find_by_id(self, pk: Any, pk_col: str = "id") -> Record | None:
        return self._db.query_one(
            f"SELECT * FROM {self._table} WHERE {pk_col} = ?", (pk,))

    def update(self, pk: Any, data: Record, pk_col: str = "id") -> int:
        sets   = ", ".join(f"{k} = ?" for k in data)
        sql    = f"UPDATE {self._table} SET {sets} WHERE {pk_col} = ?"
        cur    = self._db.execute(sql, (*data.values(), pk))
        return cur.rowcount

    def delete(self, pk: Any, pk_col: str = "id") -> int:
        cur = self._db.execute(
            f"DELETE FROM {self._table} WHERE {pk_col} = ?", (pk,))
        return cur.rowcount

    def count(self, where: str | None = None, params: tuple = ()) -> int:
        sql = f"SELECT COUNT(*) AS n FROM {self._table}"
        if where:
            sql += f" WHERE {where}"
        row = self._db.query_one(sql, params)
        return row["n"] if row else 0

# ── Demo ──────────────────────────────────────────────────────
if __name__ == "__main__":
    db = DatabaseManager(":memory:").connect()

    # Migration
    m = Migration(db)
    m.apply(1, "create_users", """
        CREATE TABLE users (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT    NOT NULL,
            email   TEXT    UNIQUE NOT NULL,
            age     INTEGER,
            active  INTEGER DEFAULT 1,
            created TEXT
        )
    """)
    m.apply(2, "create_products", """
        CREATE TABLE products (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT    NOT NULL,
            price   REAL    NOT NULL,
            stock   INTEGER DEFAULT 0
        )
    """)
    print(f"Schema version: {m.current_version()}")

    # Repository
    users = Repository(db, "users")
    users.insert_many([
        {"name": "Alice",   "email": "alice@ex.com",   "age": 30, "created": datetime.now().isoformat()},
        {"name": "Bob",     "email": "bob@ex.com",     "age": 25, "created": datetime.now().isoformat()},
        {"name": "Charlie", "email": "charlie@ex.com", "age": 35, "created": datetime.now().isoformat()},
    ])
    print(f"Total users: {users.count()}")

    # QueryBuilder
    q = (QueryBuilder("users")
         .select("id", "name", "age")
         .where("age > ?", 25)
         .order_by("name")
         .limit(10))
    sql, params = q.build()
    print(f"\nSQL: {sql}")
    print(f"Params: {params}")
    print(q.run(db))

    # Update
    users.update(1, {"age": 31})
    print("\nUpdated:", users.find_by_id(1))

    # Delete
    users.delete(3)
    print(f"After delete: {users.count()} users")

    db.close()
