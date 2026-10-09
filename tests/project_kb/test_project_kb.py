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
from semantica.project_kb.service import ProjectKnowledgeService
from semantica.project_kb.store import Store


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
            assert {tool.name for tool in tools.tools} == {"project_summary", "find_symbol", "analyze_impact"}
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
