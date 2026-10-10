from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import yaml

from .decisions import load_decisions, proposal_payload
from .extractor import Extractor
from .git_source import GitSource
from .graph import publish
from .store import Store


CONFIG_FILE = "project-kb.json"
STATE_FILE = "update-state.json"


def config_path(output: Path) -> Path:
    return output / CONFIG_FILE


def load_config(output: Path) -> dict[str, Any]:
    path = config_path(output)
    if not path.exists():
        raise FileNotFoundError(f"Knowledge-base config not found: {path}. Run build first.")
    return json.loads(path.read_text(encoding="utf-8"))


def save_config(config: dict[str, Any]) -> None:
    output = Path(config["output"])
    output.mkdir(parents=True, exist_ok=True)
    temporary = output / f"{CONFIG_FILE}.tmp"
    temporary.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(config_path(output))


def _decision_digest(source: GitSource, inbox: Path) -> str:
    digest = hashlib.sha256()
    for path, sha in sorted(source.files().items()):
        if path.startswith(".semantica/decisions/") and path.endswith((".yaml", ".yml")):
            digest.update(path.encode("utf-8"))
            digest.update(sha.encode("ascii"))
    if inbox.exists():
        for path in sorted([*inbox.glob("*.yaml"), *inbox.glob("*.yml")]):
            digest.update(path.name.encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()


def signature(config: dict[str, Any]) -> tuple[GitSource, str]:
    output = Path(config["output"])
    source = GitSource(Path(config["repo"]), config.get("revision", "HEAD"))
    decision_digest = _decision_digest(source, output / "decision-inbox")
    value = hashlib.sha256(
        f"{source.snapshot.commit_sha}|{decision_digest}|{config.get('roots', [])}|{config.get('depth', 3)}".encode("utf-8")
    ).hexdigest()
    return source, value


def build_project(config: dict[str, Any], force: bool = False) -> dict[str, Any]:
    output = Path(config["output"]).resolve()
    database = output / "project_kb.sqlite3"
    artifacts = output / "artifacts"
    source, current_signature = signature(config)
    state_path = output / STATE_FILE
    if not force and state_path.exists():
        previous = json.loads(state_path.read_text(encoding="utf-8"))
        if previous.get("signature") == current_signature:
            return {
                "status": "skipped",
                "reason": "Git revision and decision inputs are unchanged",
                "snapshot_id": source.snapshot.snapshot_id,
            }
    store = Store(database)
    with store.transaction():
        extraction = Extractor(source, store, config.get("name") or source.repository.name).build()
        extraction["counts"].update(load_decisions(source, store, output / "decision-inbox"))
    artifact_dir = artifacts / source.snapshot.commit_sha
    manifest = publish(
        store, source.snapshot.snapshot_id, artifact_dir,
        list(config.get("roots") or []), int(config.get("depth", 3)),
    )
    current_path = artifacts / "current.json"
    temporary_current = artifacts / "current.tmp.json"
    temporary_current.write_text(
        json.dumps({"snapshot_id": source.snapshot.snapshot_id,
                    "manifest": str(artifact_dir / "manifest.json")}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary_current.replace(current_path)
    state = {
        "signature": current_signature,
        "snapshot_id": source.snapshot.snapshot_id,
        "commit_sha": source.snapshot.commit_sha,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    temporary_state = output / f"{STATE_FILE}.tmp"
    temporary_state.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary_state.replace(state_path)
    return {
        "status": "updated",
        "extraction": extraction,
        "publication": manifest,
        "database": str(database),
        "current": str(current_path),
    }


def watch(output: Path, interval: float = 5.0, once: bool = False) -> None:
    config = load_config(output)
    last_seen: str | None = None
    while True:
        try:
            _source, current = signature(config)
            if current != last_seen:
                result = build_project(config)
                print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)
                last_seen = current
        except Exception as error:
            print(json.dumps({"status": "error", "error": str(error)}, ensure_ascii=False), flush=True)
        if once:
            return
        time.sleep(interval)


def propose_decision(
    output: Path,
    decision_id: str,
    question: str,
    chosen_solution: str,
    rationale: str,
    affected_symbols: list[str] | None = None,
    alternatives: list[str] | None = None,
    constraints: list[str] | None = None,
    created_by: str = "agent",
) -> dict[str, Any]:
    payload = proposal_payload(
        decision_id, question, chosen_solution, rationale,
        affected_symbols, alternatives, constraints, created_by,
    )
    inbox = output / "decision-inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    path = inbox / f"{payload['decision_id']}.yaml"
    if path.exists():
        raise FileExistsError(f"Decision proposal already exists: {path}")
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return {
        "status": "proposed",
        "path": str(path),
        "review_status": "pending",
        "next_step": "Run update, or keep watch running. Confirm with decision-accept before committing as project history.",
    }


def accept_decision(output: Path, repository: Path, decision_id: str) -> dict[str, Any]:
    inbox_path = output / "decision-inbox" / f"{decision_id}.yaml"
    if not inbox_path.exists():
        raise FileNotFoundError(f"Decision proposal not found: {inbox_path}")
    payload = yaml.safe_load(inbox_path.read_text(encoding="utf-8"))
    payload["review_status"] = "confirmed"
    payload["created_by"] = payload.get("created_by") or "agent"
    target_dir = repository / ".semantica" / "decisions"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / inbox_path.name
    target.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return {
        "status": "accepted_to_worktree",
        "path": str(target),
        "next_step": "Review the YAML, then git add and commit it. The next update will use the committed project record.",
    }


def write_decision_template(repository: Path) -> Path:
    target = repository / ".semantica" / "decisions" / "decision-template.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        payload = proposal_payload(
            "decision-stable-id", "What problem is being solved?",
            "Describe the chosen solution.", "Explain why this solution was chosen.",
            ["RelatedClassOrMethod"], ["Rejected alternative"],
            ["Performance or compatibility constraint"], "human",
        )
        payload["template"] = True
        target.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return target
