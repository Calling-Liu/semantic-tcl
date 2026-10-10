from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .git_source import GitSource
from .store import Store


DECISION_PREFIX = ".semantica/decisions/"


def _decision_id(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9._:-]+", "-", value.strip()).strip("-")
    if not normalized:
        normalized = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return normalized


def _load_yaml(text: str, source_path: str, source_kind: str) -> dict[str, Any] | None:
    item = yaml.safe_load(text)
    if not isinstance(item, dict) or item.get("template"):
        return None
    question = str(item.get("question", "")).strip()
    chosen = str(item.get("chosen_solution", "")).strip()
    rationale = str(item.get("rationale", "")).strip()
    if not question or not chosen or not rationale:
        raise ValueError(f"Decision requires question, chosen_solution and rationale: {source_path}")
    identifier = _decision_id(str(item.get("decision_id") or item.get("id") or question))
    return {
        "decision_id": identifier,
        "question": question,
        "chosen_solution": chosen,
        "rationale": rationale,
        "alternatives": list(item.get("alternatives") or []),
        "constraints": list(item.get("constraints") or []),
        "affected_symbols": list(item.get("affected_symbols") or item.get("affected_names") or []),
        "review_status": str(item.get("review_status") or "pending"),
        "decision_status": str(item.get("decision_status") or "active"),
        "confidence_score": item.get("confidence_score"),
        "source_kind": source_kind,
        "source_path": source_path,
        "created_by": str(item.get("created_by") or "human"),
        "created_at": str(item.get("created_at") or datetime.now(timezone.utc).isoformat()),
    }


def load_decisions(source: GitSource, store: Store, inbox: Path) -> dict[str, int]:
    records: dict[str, dict[str, Any]] = {}
    project_paths = [
        path for path in source.files()
        if path.startswith(DECISION_PREFIX) and path.endswith((".yaml", ".yml"))
    ]
    source.preload(project_paths)
    for path in project_paths:
        record = _load_yaml(source.text(path), path, "project_git")
        if record:
            records[record["decision_id"]] = record
    inbox.mkdir(parents=True, exist_ok=True)
    for path in sorted([*inbox.glob("*.yaml"), *inbox.glob("*.yml")]):
        record = _load_yaml(path.read_text(encoding="utf-8"), str(path), "agent_inbox")
        if record and record["decision_id"] not in records:
            records[record["decision_id"]] = record
    linked = 0
    for record in records.values():
        decision_node = f"decision:{record['decision_id']}"
        store.execute(
            "INSERT OR REPLACE INTO decisions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                source.snapshot.snapshot_id, record["decision_id"], record["question"],
                record["chosen_solution"], record["rationale"], store.json(record["alternatives"]),
                store.json(record["constraints"]), store.json(record["affected_symbols"]),
                record["review_status"], record["decision_status"], record["confidence_score"],
                record["source_kind"], record["source_path"], record["created_by"], record["created_at"],
            ),
        )
        store.execute(
            "INSERT OR REPLACE INTO entities VALUES(?,?,?,?,?,?,?,?)",
            (
                source.snapshot.snapshot_id, decision_node, "architecture_decision",
                record["question"], "decision", record["source_path"], None,
                store.json({
                    "chosen_solution": record["chosen_solution"],
                    "rationale": record["rationale"],
                    "review_status": record["review_status"],
                    "decision_status": record["decision_status"],
                    "source_kind": record["source_kind"],
                }),
            ),
        )
        for query in record["affected_symbols"]:
            matches = store.query(
                "SELECT symbol_id FROM symbols WHERE snapshot_id=? AND (name=? OR fqn=?)",
                (source.snapshot.snapshot_id, query, query),
            )
            for match in matches:
                relation_id = hashlib.sha256(
                    f"{source.snapshot.snapshot_id}|{decision_node}|{match['symbol_id']}|AFFECTS".encode("utf-8")
                ).hexdigest()
                store.execute(
                    "INSERT OR REPLACE INTO relations VALUES(?,?,?,?,?,?,?,?,?)",
                    (
                        source.snapshot.snapshot_id, relation_id, decision_node,
                        match["symbol_id"], query, "AFFECTS", "DECLARED", "RESOLVED",
                        record["source_path"],
                    ),
                )
                linked += 1
    return {"decisions": len(records), "decision_links": linked}


def proposal_payload(
    decision_id: str,
    question: str,
    chosen_solution: str,
    rationale: str,
    affected_symbols: list[str] | None = None,
    alternatives: list[str] | None = None,
    constraints: list[str] | None = None,
    created_by: str = "agent",
) -> dict[str, Any]:
    return {
        "decision_id": _decision_id(decision_id),
        "question": question,
        "chosen_solution": chosen_solution,
        "rationale": rationale,
        "alternatives": alternatives or [],
        "constraints": constraints or [],
        "affected_symbols": affected_symbols or [],
        "review_status": "pending",
        "decision_status": "active",
        "confidence_score": None,
        "created_by": created_by,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
