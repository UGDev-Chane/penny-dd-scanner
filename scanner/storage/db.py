from __future__ import annotations
import sqlite3
from pathlib import Path

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  started_at TEXT NOT NULL,
  git_commit TEXT,
  config_hash TEXT
);

CREATE TABLE IF NOT EXISTS tickers (
  symbol TEXT PRIMARY KEY,
  exchange TEXT,
  cik TEXT
);

CREATE TABLE IF NOT EXISTS daily_bars (
  symbol TEXT NOT NULL,
  date TEXT NOT NULL,
  open REAL,
  high REAL,
  low REAL,
  close REAL,
  volume REAL,
  dollar_volume REAL,
  PRIMARY KEY (symbol, date)
);

CREATE TABLE IF NOT EXISTS filings (
  cik TEXT NOT NULL,
  accession TEXT NOT NULL,
  form TEXT NOT NULL,
  filed_at TEXT NOT NULL,
  primary_doc TEXT,
  url TEXT,
  PRIMARY KEY (cik, accession)
);

CREATE TABLE IF NOT EXISTS scores_daily (
  symbol TEXT NOT NULL,
  date TEXT NOT NULL,
  score_total REAL NOT NULL,
  components_json TEXT NOT NULL,
  setup_class TEXT NOT NULL,
  PRIMARY KEY (symbol, date)
);

CREATE TABLE IF NOT EXISTS signals (
  symbol TEXT NOT NULL,
  date TEXT NOT NULL,
  signal TEXT NOT NULL,
  rationale_json TEXT NOT NULL,
  PRIMARY KEY (symbol, date, signal)
);

CREATE TABLE IF NOT EXISTS dd_notes (
  symbol TEXT NOT NULL,
  date TEXT NOT NULL,
  model TEXT NOT NULL,
  note_md TEXT NOT NULL,
  PRIMARY KEY (symbol, date)
);
"""

def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA foreign_keys=ON;")
    return con

def init_db(con: sqlite3.Connection) -> None:
    con.executescript(SCHEMA_SQL)
    con.commit()

def sqlite_upsert_daily_bars(table, conn, keys, data_iter):
    """
    Pandas to_sql UPSERT helper for SQLite.

    Assumes UNIQUE(symbol, date) constraint exists.
    """
    data = list(data_iter)
    if not data:
        return 0

    columns = ",".join([f'"{k}"' for k in keys])
    placeholders = ",".join(["?"] * len(keys))

    conflict_keys = {"symbol", "date"}
    update_cols = [k for k in keys if k not in conflict_keys]

    set_clause = ", ".join(
        [f'"{c}"=excluded."{c}"' for c in update_cols]
    )

    sql = f"""
    INSERT INTO {table.name} ({columns})
    VALUES ({placeholders})
    ON CONFLICT(symbol, date) DO UPDATE SET
        {set_clause}
    """

    conn.executemany(sql, data)
    return len(data)
