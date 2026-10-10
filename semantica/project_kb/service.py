from __future__ import annotations

from pathlib import Path
from typing import Any

from .store import Store


class ProjectKnowledgeService:
    def __init__(self, database: Path) -> None:
        self.store = Store(database)

    def snapshot_id(self) -> str:
        rows = self.store.query(
            "SELECT snapshot_id FROM snapshots WHERE status='ready' ORDER BY created_at DESC LIMIT 1"
        )
        if not rows:
            raise RuntimeError("No ready project knowledge snapshot")
        return rows[0]["snapshot_id"]

    def find_symbol(self, query: str, limit: int = 20) -> dict[str, Any]:
        snapshot_id = self.snapshot_id()
        rows = self.store.query(
            """
            SELECT * FROM symbols WHERE snapshot_id=?
              AND (name LIKE ? OR fqn LIKE ? OR symbol_id LIKE ?)
            ORDER BY CASE WHEN name=? THEN 0 ELSE 1 END, name LIMIT ?
            """,
            (snapshot_id, f"%{query}%", f"%{query}%", f"%{query}%", query, limit),
        )
        return {"snapshot_id": snapshot_id, "results": rows}

    def analyze_impact(self, query: str, limit: int = 100) -> dict[str, Any]:
        snapshot_id = self.snapshot_id()
        symbols = self.find_symbol(query, 20)["results"]
        exact = [item for item in symbols if item["name"] == query or item["fqn"] == query]
        if exact:
            symbols = exact
        entities = self.store.query(
            "SELECT * FROM entities WHERE snapshot_id=? AND name LIKE ? LIMIT 20",
            (snapshot_id, f"%{query}%"),
        )
        target_ids = [item["symbol_id"] for item in symbols] + [item["entity_id"] for item in entities]
        if not target_ids:
            return {"snapshot_id": snapshot_id, "query": query, "symbols": [], "entities": [], "relations": []}
        placeholders = ",".join("?" for _ in target_ids)
        relations = self.store.query(
            f"""
            SELECT * FROM relations WHERE snapshot_id=?
              AND (source_id IN ({placeholders}) OR target_id IN ({placeholders}))
            ORDER BY CASE WHEN evidence_kind='DECLARED' THEN 0 ELSE 1 END,
                     relation_type LIMIT ?
            """,
            (snapshot_id, *target_ids, *target_ids, limit),
        )
        return {
            "snapshot_id": snapshot_id, "query": query, "symbols": symbols,
            "entities": entities, "relations": relations,
            "note": "STATIC/DECLARED relations are not OBSERVED runtime proof; UNRESOLVED edges require review.",
        }

    def project_summary(self) -> dict[str, Any]:
        snapshot_id = self.snapshot_id()
        snapshot = self.store.query("SELECT * FROM snapshots WHERE snapshot_id=?", (snapshot_id,))[0]
        counts = {
            "modules": self.store.query("SELECT count(*) value FROM modules WHERE snapshot_id=?", (snapshot_id,))[0]["value"],
            "symbols": self.store.query("SELECT count(*) value FROM symbols WHERE snapshot_id=?", (snapshot_id,))[0]["value"],
            "entities": self.store.query("SELECT count(*) value FROM entities WHERE snapshot_id=?", (snapshot_id,))[0]["value"],
            "relations": self.store.query("SELECT count(*) value FROM relations WHERE snapshot_id=?", (snapshot_id,))[0]["value"],
        }
        languages = self.store.query(
            "SELECT language, count(*) count FROM symbols WHERE snapshot_id=? GROUP BY language ORDER BY count DESC",
            (snapshot_id,),
        )
        counts["decisions"] = self.store.query(
            "SELECT count(*) value FROM decisions WHERE snapshot_id=?", (snapshot_id,)
        )[0]["value"]
        return {"snapshot": snapshot, "counts": counts, "languages": languages}

    def list_decisions(self, review_status: str | None = None) -> dict[str, Any]:
        snapshot_id = self.snapshot_id()
        if review_status:
            rows = self.store.query(
                "SELECT * FROM decisions WHERE snapshot_id=? AND review_status=? ORDER BY created_at DESC",
                (snapshot_id, review_status),
            )
        else:
            rows = self.store.query(
                "SELECT * FROM decisions WHERE snapshot_id=? ORDER BY created_at DESC",
                (snapshot_id,),
            )
        return {"snapshot_id": snapshot_id, "results": rows}
