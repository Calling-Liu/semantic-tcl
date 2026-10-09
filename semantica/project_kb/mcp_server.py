from __future__ import annotations

from pathlib import Path

from mcp.server.mcpserver import MCPServer

from .service import ProjectKnowledgeService


def create_server(database: Path) -> MCPServer:
    service = ProjectKnowledgeService(database)
    server = MCPServer(
        "semantica-project-kb",
        instructions="Read-only Git-native project symbols, declared contracts, and impact relations.",
    )

    @server.tool()
    def project_summary() -> dict:
        """Return snapshot, module, symbol, entity, relation, and language counts."""
        return service.project_summary()

    @server.tool()
    def find_symbol(query: str, limit: int = 20) -> dict:
        """Find Java or Kotlin symbols from the immutable Git snapshot."""
        return service.find_symbol(query, limit)

    @server.tool()
    def analyze_impact(query: str, limit: int = 100) -> dict:
        """Return static and declared code, Gradle, AIDL, Manifest, and ProGuard impacts."""
        return service.analyze_impact(query, limit)

    return server


def run(database: Path) -> None:
    create_server(database).run(transport="stdio")
