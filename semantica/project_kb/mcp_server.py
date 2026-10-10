from __future__ import annotations

from pathlib import Path

from mcp.server.mcpserver import MCPServer

from .service import ProjectKnowledgeService
from .workflow import propose_decision


def create_server(database: Path, output: Path | None = None,
                  allow_decision_proposals: bool = False) -> MCPServer:
    service = ProjectKnowledgeService(database)
    server = MCPServer(
        "semantica-project-kb",
        instructions=(
            "Git-native project symbols, declared contracts, impacts, and decisions. "
            + ("Decision proposal writes are enabled; proposals remain pending."
               if allow_decision_proposals else "This server is read-only.")
        ),
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

    @server.tool()
    def list_decisions(review_status: str | None = None) -> dict:
        """List confirmed or pending project decisions."""
        return service.list_decisions(review_status)

    if allow_decision_proposals:
        if output is None:
            raise ValueError("output is required when decision proposals are enabled")

        @server.tool()
        def propose_decision_candidate(
            decision_id: str,
            question: str,
            chosen_solution: str,
            rationale: str,
            affected_symbols: list[str] | None = None,
            alternatives: list[str] | None = None,
            constraints: list[str] | None = None,
        ) -> dict:
            """Write a pending Agent decision candidate to the review inbox."""
            return propose_decision(
                output, decision_id, question, chosen_solution, rationale,
                affected_symbols, alternatives, constraints, "agent",
            )

    return server


def run(database: Path, output: Path | None = None,
        allow_decision_proposals: bool = False) -> None:
    create_server(database, output, allow_decision_proposals).run(transport="stdio")
