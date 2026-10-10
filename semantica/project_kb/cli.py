from __future__ import annotations

import argparse
import json
from pathlib import Path

from .mcp_server import run as run_mcp
from .service import ProjectKnowledgeService
from .workflow import (
    accept_decision,
    build_project,
    load_config,
    propose_decision,
    save_config,
    watch,
    write_decision_template,
)


def _paths(output: Path) -> tuple[Path, Path]:
    return output / "project_kb.sqlite3", output / "artifacts"


def build_command(args: argparse.Namespace) -> None:
    repository = args.repo.resolve()
    output = args.output.resolve()
    config = {
        "repo": str(repository), "output": str(output),
        "name": args.name or repository.name, "revision": args.revision,
        "roots": args.roots, "depth": args.depth,
    }
    save_config(config)
    print(json.dumps(build_project(config, force=True), indent=2, ensure_ascii=False))


def update_command(args: argparse.Namespace) -> None:
    config = load_config(args.output.resolve())
    print(json.dumps(build_project(config, force=args.force), indent=2, ensure_ascii=False))


def watch_command(args: argparse.Namespace) -> None:
    watch(args.output.resolve(), args.interval, args.once)


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

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("--output", type=Path, required=True)
    update_parser.add_argument("--force", action="store_true")
    update_parser.set_defaults(handler=update_command)

    watch_parser = subparsers.add_parser("watch")
    watch_parser.add_argument("--output", type=Path, required=True)
    watch_parser.add_argument("--interval", type=float, default=5.0)
    watch_parser.add_argument("--once", action="store_true")
    watch_parser.set_defaults(handler=watch_command)

    for command in ("find", "impact"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("--output", type=Path, required=True)
        command_parser.add_argument("query")
        command_parser.add_argument("--limit", type=int, default=100 if command == "impact" else 20)

    summary_parser = subparsers.add_parser("summary")
    summary_parser.add_argument("--output", type=Path, required=True)
    mcp_parser = subparsers.add_parser("mcp")
    mcp_parser.add_argument("--output", type=Path, required=True)
    mcp_parser.add_argument("--allow-decision-proposals", action="store_true")

    decisions_parser = subparsers.add_parser("decisions")
    decisions_parser.add_argument("--output", type=Path, required=True)
    decisions_parser.add_argument("--review-status")

    template_parser = subparsers.add_parser("decision-template")
    template_parser.add_argument("--repo", type=Path, required=True)

    propose_parser = subparsers.add_parser("decision-propose")
    propose_parser.add_argument("--output", type=Path, required=True)
    propose_parser.add_argument("--id", required=True)
    propose_parser.add_argument("--question", required=True)
    propose_parser.add_argument("--solution", required=True)
    propose_parser.add_argument("--rationale", required=True)
    propose_parser.add_argument("--affected", nargs="*", default=[])
    propose_parser.add_argument("--alternative", action="append", default=[])
    propose_parser.add_argument("--constraint", action="append", default=[])

    accept_parser = subparsers.add_parser("decision-accept")
    accept_parser.add_argument("--output", type=Path, required=True)
    accept_parser.add_argument("--repo", type=Path, required=True)
    accept_parser.add_argument("decision_id")

    args = parser.parse_args()
    if hasattr(args, "handler"):
        args.handler(args)
        return
    if args.command == "decision-template":
        print(write_decision_template(args.repo.resolve()))
        return
    if args.command == "decision-propose":
        result = propose_decision(
            args.output.resolve(), args.id, args.question, args.solution,
            args.rationale, args.affected, args.alternative, args.constraint,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    database, _artifacts = _paths(args.output.resolve())
    if args.command == "mcp":
        run_mcp(database, args.output.resolve(), args.allow_decision_proposals)
        return
    if args.command == "decision-accept":
        result = accept_decision(args.output.resolve(), args.repo.resolve(), args.decision_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    service = ProjectKnowledgeService(database)
    if args.command == "find":
        result = service.find_symbol(args.query, args.limit)
    elif args.command == "impact":
        result = service.analyze_impact(args.query, args.limit)
    elif args.command == "decisions":
        result = service.list_decisions(args.review_status)
    else:
        result = service.project_summary()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
