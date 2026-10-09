from __future__ import annotations

import hashlib
import json
from collections import deque
from pathlib import Path
from typing import Any

from semantica.context import ContextGraph

from .store import Store


def _digest(data: dict[str, Any]) -> str:
    nodes = sorted(
        ({"id": node["id"], "type": node["type"], "content": node.get("content"),
          "properties": node.get("properties", node.get("metadata", {}))}
         for node in data.get("nodes", [])), key=lambda item: item["id"],
    )
    edges = sorted(
        ({"source": edge.get("source_id", edge.get("source")),
          "target": edge.get("target_id", edge.get("target")), "type": edge["type"],
          "properties": edge.get("properties", edge.get("metadata", {}))}
         for edge in data.get("edges", [])),
        key=lambda item: (item["source"], item["target"], item["type"],
                          json.dumps(item["properties"], sort_keys=True, ensure_ascii=False)),
    )
    canonical = json.dumps({"nodes": nodes, "edges": edges}, sort_keys=True,
                           ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def publish(store: Store, snapshot_id: str, output: Path,
            roots: list[str], depth: int = 3) -> dict[str, Any]:
    graph = ContextGraph(advanced_analytics=False)
    root_rows: list[dict[str, Any]] = []
    for root in roots:
        exact = store.query(
            "SELECT * FROM symbols WHERE snapshot_id=? AND (name=? OR fqn=?) ORDER BY kind",
            (snapshot_id, root, root),
        )
        root_rows.extend(exact or store.query(
            "SELECT * FROM symbols WHERE snapshot_id=? AND name LIKE ? ORDER BY name LIMIT 10",
            (snapshot_id, f"%{root}%"),
        ))
    selected = {row["symbol_id"] for row in root_rows}
    queue = deque((symbol_id, 0) for symbol_id in selected)
    while queue:
        current, current_depth = queue.popleft()
        if current_depth >= depth:
            continue
        for relation in store.query(
            "SELECT * FROM relations WHERE snapshot_id=? AND source_id=? AND resolution_status='RESOLVED'",
            (snapshot_id, current),
        ):
            target = relation["target_id"]
            if target and target not in selected and target.startswith(("java:", "kotlin:")):
                selected.add(target)
                queue.append((target, current_depth + 1))
    for symbol_id in list(selected):
        if "#" in symbol_id:
            selected.add(symbol_id.split("#", 1)[0])
    if not selected:
        selected.update(row["symbol_id"] for row in store.query(
            "SELECT symbol_id FROM symbols WHERE snapshot_id=? AND kind<>'method' AND accessibility='public' LIMIT 300",
            (snapshot_id,),
        ))
    placeholders = ",".join("?" for _ in selected) or "''"
    symbols = store.query(
        f"SELECT * FROM symbols WHERE snapshot_id=? AND symbol_id IN ({placeholders})",
        (snapshot_id, *sorted(selected)),
    )
    node_ids: set[str] = set()
    modules: set[str] = set()
    for symbol in symbols:
        node_ids.add(symbol["symbol_id"])
        modules.add(symbol["module"])
        graph.add_node(symbol["symbol_id"], symbol["kind"], symbol["signature"],
                       name=symbol["name"], language=symbol["language"], module=symbol["module"],
                       fqn=symbol["fqn"], source_path=symbol["source_path"],
                       source_line=symbol["source_line"], parser=symbol["parser"])
    entities = store.query("SELECT * FROM entities WHERE snapshot_id=?", (snapshot_id,))
    for entity in entities:
        node_ids.add(entity["entity_id"])
        modules.add(entity["module"])
        graph.add_node(entity["entity_id"], entity["kind"], entity["name"],
                       name=entity["name"], module=entity["module"],
                       source_path=entity["source_path"], source_line=entity["source_line"],
                       metadata=json.loads(entity["metadata_json"]))
    module_rows = store.query("SELECT * FROM modules WHERE snapshot_id=?", (snapshot_id,))
    module_ids: dict[str, str] = {}
    for module in module_rows:
        if module["name"] in modules:
            node_ids.add(module["module_id"])
            module_ids[module["name"]] = module["module_id"]
            graph.add_node(module["module_id"], "module", module["name"],
                           name=module["name"], path=module["path"])
    for relation in store.query("SELECT * FROM relations WHERE snapshot_id=?", (snapshot_id,)):
        target = relation["target_id"]
        if relation["source_id"] in node_ids and target in node_ids:
            graph.add_edge(relation["source_id"], target, relation["relation_type"].lower(),
                           evidence_kind=relation["evidence_kind"],
                           resolution_status=relation["resolution_status"],
                           source_path=relation["source_path"])
    output.mkdir(parents=True, exist_ok=True)
    graph_path = output / "context_graph.json"
    temp_graph = output / "context_graph.tmp.json"
    graph.save_to_file(temp_graph)
    reloaded = ContextGraph(advanced_analytics=False)
    reloaded.load_from_file(temp_graph)
    if reloaded.stats()["node_count"] != graph.stats()["node_count"]:
        raise RuntimeError("ContextGraph reload validation failed")
    temp_graph.replace(graph_path)
    digest = _digest(graph.to_dict())
    manifest = {
        "snapshot_id": snapshot_id, "graph_path": str(graph_path),
        "graph_digest": digest, "roots": roots, "graph_stats": graph.stats(),
    }
    manifest_path = output / "manifest.json"
    temp_manifest = output / "manifest.tmp.json"
    temp_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    temp_manifest.replace(manifest_path)
    store.execute("INSERT OR REPLACE INTO publications VALUES(?,?,?, ?,CURRENT_TIMESTAMP)",
                  (snapshot_id, str(graph_path), digest, str(manifest_path)))
    return manifest
