from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from semantica.context import ContextGraph
from semantica.project_kb.extractor import Extractor
from semantica.project_kb.git_source import GitSource
from semantica.project_kb.graph import publish
from semantica.project_kb.mcp_server import create_server
from semantica.project_kb.service import ProjectKnowledgeService
from semantica.project_kb.store import Store
from semantica.project_kb.workflow import (
    accept_decision,
    build_project,
    propose_decision,
    save_config,
    watch,
)


ROOT = Path(__file__).resolve().parents[2]


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _fixture_repo() -> Path:
    path = ROOT / ".test-output" / f"fixture-{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    _write(path / "settings.gradle", "include ':app'\n")
    _write(path / "app/build.gradle", "plugins { id 'com.android.library' }\n")
    _write(
        path / "app/src/main/java/demo/Controller.java",
        "package demo; public class Controller { public void start(){ helper(); } private void helper(){} }\n",
    )
    _write(
        path / "app/src/main/java/demo/Host.kt",
        "package demo\nclass Host { fun render(value: String) = value }\n",
    )
    _write(
        path / "app/src/main/AndroidManifest.xml",
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="demo"><application><service android:name=".Controller" android:exported="false"/></application></manifest>',
    )
    _write(path / "app/proguard-rules.pro", "-keep class demo.Controller { *; }\n")
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=path, check=True, capture_output=True)
    return path


def test_build_query_and_graph_reload() -> None:
    repository = _fixture_repo()
    output = ROOT / ".test-output" / f"output-{uuid.uuid4().hex}"
    try:
        source = GitSource(repository)
        store = Store(output / "project_kb.sqlite3")
        report = Extractor(source, store, "fixture").build()
        manifest = publish(store, source.snapshot.snapshot_id, output / "artifacts", ["Controller", "Host"], 2)
        assert report["counts"]["java_files"] == 1
        assert report["counts"]["kotlin_files"] == 1
        service = ProjectKnowledgeService(output / "project_kb.sqlite3")
        assert service.find_symbol("Controller")["results"]
        impact = service.analyze_impact("Controller")
        assert {row["relation_type"] for row in impact["relations"]} >= {"REGISTERS_COMPONENT", "PROTECTS"}
        graph = ContextGraph(advanced_analytics=False)
        graph.load_from_file(manifest["graph_path"])
        assert graph.stats()["node_count"] > 0
    finally:
        shutil.rmtree(repository, ignore_errors=True)
        shutil.rmtree(output, ignore_errors=True)


async def _mcp_call(database: Path) -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT)
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "semantica.project_kb.cli", "mcp", "--output", str(database.parent)],
        env=environment,
    )
    async with stdio_client(parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert {tool.name for tool in tools.tools} == {
                "project_summary", "find_symbol", "analyze_impact", "list_decisions",
            }
            result = await session.call_tool("project_summary", {})
            assert not result.is_error
            assert json.loads(result.content[0].text)["counts"]["symbols"] > 0


def test_stdio_mcp() -> None:
    repository = _fixture_repo()
    output = ROOT / ".test-output" / f"mcp-{uuid.uuid4().hex}"
    try:
        source = GitSource(repository)
        store = Store(output / "project_kb.sqlite3")
        Extractor(source, store, "fixture").build()
        asyncio.run(_mcp_call(output / "project_kb.sqlite3"))
    finally:
        shutil.rmtree(repository, ignore_errors=True)
        shutil.rmtree(output, ignore_errors=True)


def test_manual_automatic_update_and_decision_review() -> None:
    repository = _fixture_repo()
    output = ROOT / ".test-output" / f"workflow-{uuid.uuid4().hex}"
    config = {
        "repo": str(repository), "output": str(output), "name": "fixture",
        "revision": "HEAD", "roots": ["Controller", "Host"], "depth": 2,
    }
    try:
        save_config(config)
        first = build_project(config, force=True)
        assert first["status"] == "updated"
        assert build_project(config)["status"] == "skipped"

        proposed = propose_decision(
            output, "bounded-worker", "How should work be bounded?",
            "Use a bounded worker queue.", "Unbounded work can exhaust resources.",
            ["Controller"], ["Create one thread per task"], ["Do not block the main thread"],
        )
        assert proposed["review_status"] == "pending"
        watch(output, interval=0.01, once=True)
        service = ProjectKnowledgeService(output / "project_kb.sqlite3")
        pending = service.list_decisions("pending")["results"]
        assert len(pending) == 1
        assert pending[0]["source_kind"] == "agent_inbox"
        read_only_tools = {
            tool.name for tool in asyncio.run(
                create_server(output / "project_kb.sqlite3").list_tools()
            )
        }
        writable_tools = {
            tool.name for tool in asyncio.run(
                create_server(output / "project_kb.sqlite3", output, True).list_tools()
            )
        }
        assert "propose_decision_candidate" not in read_only_tools
        assert "propose_decision_candidate" in writable_tools

        accepted = accept_decision(output, repository, "bounded-worker")
        accepted_path = Path(accepted["path"])
        assert accepted_path.exists()
        subprocess.run(["git", "add", ".semantica/decisions/bounded-worker.yaml"], cwd=repository, check=True)
        subprocess.run(["git", "commit", "-m", "record decision"], cwd=repository,
                       check=True, capture_output=True)
        updated = build_project(config)
        assert updated["status"] == "updated"
        confirmed = service.list_decisions("confirmed")["results"]
        assert len(confirmed) == 1
        assert confirmed[0]["source_kind"] == "project_git"
    finally:
        shutil.rmtree(repository, ignore_errors=True)
        shutil.rmtree(output, ignore_errors=True)
