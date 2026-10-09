from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS snapshots(
  snapshot_id TEXT PRIMARY KEY, project_name TEXT NOT NULL, repository TEXT NOT NULL,
  commit_sha TEXT NOT NULL, branch TEXT NOT NULL, revision TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS modules(
  snapshot_id TEXT NOT NULL, module_id TEXT NOT NULL, name TEXT NOT NULL, path TEXT NOT NULL,
  PRIMARY KEY(snapshot_id,module_id)
);
CREATE TABLE IF NOT EXISTS symbols(
  snapshot_id TEXT NOT NULL, symbol_id TEXT NOT NULL, kind TEXT NOT NULL,
  language TEXT NOT NULL, module TEXT NOT NULL, fqn TEXT NOT NULL, name TEXT NOT NULL,
  signature TEXT NOT NULL, source_path TEXT NOT NULL, source_line INTEGER,
  accessibility TEXT NOT NULL, parser TEXT NOT NULL,
  PRIMARY KEY(snapshot_id,symbol_id)
);
CREATE INDEX IF NOT EXISTS idx_project_kb_symbol_name ON symbols(snapshot_id,name);
CREATE TABLE IF NOT EXISTS entities(
  snapshot_id TEXT NOT NULL, entity_id TEXT NOT NULL, kind TEXT NOT NULL,
  name TEXT NOT NULL, module TEXT NOT NULL, source_path TEXT NOT NULL,
  source_line INTEGER, metadata_json TEXT NOT NULL,
  PRIMARY KEY(snapshot_id,entity_id)
);
CREATE TABLE IF NOT EXISTS relations(
  snapshot_id TEXT NOT NULL, relation_id TEXT NOT NULL, source_id TEXT NOT NULL,
  target_id TEXT, target_text TEXT, relation_type TEXT NOT NULL,
  evidence_kind TEXT NOT NULL, resolution_status TEXT NOT NULL, source_path TEXT NOT NULL,
  PRIMARY KEY(snapshot_id,relation_id)
);
CREATE INDEX IF NOT EXISTS idx_project_kb_relation_source ON relations(snapshot_id,source_id);
CREATE INDEX IF NOT EXISTS idx_project_kb_relation_target ON relations(snapshot_id,target_id);
CREATE TABLE IF NOT EXISTS publications(
  snapshot_id TEXT PRIMARY KEY, graph_path TEXT NOT NULL, graph_digest TEXT NOT NULL,
  manifest_path TEXT NOT NULL, published_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


class Store:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        self.transaction_depth = 0
        self.connection.executescript(SCHEMA)

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        with self.lock:
            self.connection.execute(sql, params)
            if self.transaction_depth == 0:
                self.connection.commit()

    def query(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self.lock:
            return [dict(row) for row in self.connection.execute(sql, params).fetchall()]

    def reset(self, snapshot_id: str) -> None:
        with self.lock:
            for table in ("relations", "entities", "symbols", "modules", "publications", "snapshots"):
                self.connection.execute(f"DELETE FROM {table} WHERE snapshot_id = ?", (snapshot_id,))
            if self.transaction_depth == 0:
                self.connection.commit()

    @contextmanager
    def transaction(self):
        with self.lock:
            outermost = self.transaction_depth == 0
            if outermost:
                self.connection.execute("BEGIN")
            self.transaction_depth += 1
            try:
                yield
                self.transaction_depth -= 1
                if outermost:
                    self.connection.commit()
            except Exception:
                self.transaction_depth -= 1
                if outermost:
                    self.connection.rollback()
                raise

    def json(self, value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    def close(self) -> None:
        with self.lock:
            self.connection.close()
