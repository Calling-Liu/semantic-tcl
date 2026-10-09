from __future__ import annotations

import argparse
import json
from pathlib import Path

from .extractor import Extractor
from .git_source import GitSource
from .graph import publish
from .mcp_server import run as run_mcp
from .service import ProjectKnowledgeService
from .store import Store


def _paths(output: Path) -> tuple[Path, Path]:
    return output / "project_kb.sqlite3", output / "artifacts"


def build_command(args: argparse.Namespace) -> None:
    repository = args.repo.resolve()
    output = args.output.resolve()
    database, artifacts = _paths(output)
    source = GitSource(repository, args.revision)
    store = Store(database)
    report = Extractor(source, store, args.name or repository.name).build()
    artifact_dir = artifacts / source.snapshot.commit_sha
    manifest = publish(store, source.snapshot.snapshot_id, artifact_dir, args.roots, args.depth)
    current = artifacts / "current.json"
    current.write_text(
        json.dumps({"snapshot_id": source.snapshot.snapshot_id,
                    "manifest": str(artifact_dir / "manifest.json")}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps({"extraction": report, "publication": manifest,
                      "database": str(database), "current": str(current)},
                     indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and query Git-native project knowledge bases")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--repo", type=Path, required=True)
    build_parser.add_argument("--output", type=Path, required=True)
    build_parser.add_argument("--revision", default="HEAD")
    build_parser.add_argument("--name")
    build_parser.add_argument("--roots", nargs="*", default=[])
    build_parser.add_argument("--depth", type=int, default=3)
    build_parser.set_defaults(handler=build_command)

    for command in ("find", "impact"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("--output", type=Path, required=True)
        command_parser.add_argument("query")
        command_parser.add_argument("--limit", type=int, default=100 if command == "impact" else 20)

    summary_parser = subparsers.add_parser("summary")
    summary_parser.add_argument("--output", type=Path, required=True)
    mcp_parser = subparsers.add_parser("mcp")
    mcp_parser.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    if hasattr(args, "handler"):
        args.handler(args)
        return
    database, _artifacts = _paths(args.output.resolve())
    if args.command == "mcp":
        run_mcp(database)
        return
    service = ProjectKnowledgeService(database)
    if args.command == "find":
        result = service.find_symbol(args.query, args.limit)
    elif args.command == "impact":
        result = service.analyze_impact(args.query, args.limit)
    else:
        result = service.project_summary()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
