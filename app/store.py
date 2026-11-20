import sqlite3
from contextlib import contextmanager
from pathlib import Path
from app import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY, source BLOB NOT NULL, book BLOB NOT NULL,
  result TEXT NOT NULL, created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reviews (
  run_id TEXT NOT NULL REFERENCES runs(id), version INTEGER NOT NULL,
  decision TEXT NOT NULL, note TEXT NOT NULL, changed TEXT NOT NULL,
  kind TEXT NOT NULL DEFAULT '复核', key TEXT, revision INTEGER, line INTEGER, digest TEXT,
  PRIMARY KEY(run_id,version)
);
"""

# A ledger volume created before adoption support keeps serving: the ruling
# columns are added in place rather than dropping the reviewer's history.
ADDED = (('kind',"TEXT NOT NULL DEFAULT '复核'"),('key','TEXT'),('revision','INTEGER'),
         ('line','INTEGER'),('digest','TEXT'))


def _migrate(db):
    columns = {row['name'] for row in db.execute('PRAGMA table_info(reviews)')}
    for name,ddl in ADDED:
        if name not in columns:
            db.execute(f'ALTER TABLE reviews ADD COLUMN {name} {ddl}')


@contextmanager
def connection():
    path = Path(settings.DB)
    path.parent.mkdir(parents=True,exist_ok=True)
    db = sqlite3.connect(path,timeout=10)
    db.row_factory = sqlite3.Row
    try:
        db.execute('PRAGMA foreign_keys = ON')
        db.executescript(SCHEMA)
        _migrate(db)
        with db:
            yield db
    finally:
        db.close()
