/**
 * src/workspaces/LineageWorkspace/LineageDiagram.tsx
 */
import { useEffect, useMemo, useState } from "react";
import { Link2 } from "lucide-react";
import { ReactFlow, Background, Controls } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

const THEME_CSS = `
  .react-flow { background: var(--ws-bg, #060d1a); }
  .react-flow__node-group {
    background: rgba(74,163,255,0.04);
    border: 1px dashed rgba(74,163,255,0.18);
    border-radius: 10px;
  }
  .react-flow__node-default {
    background: rgba(6,13,26,0.92);
    color: var(--ws-text, #ddeeff);
    border: 1px solid rgba(74,163,255,0.22);
    border-radius: 8px;
    padding: 10px 12px;
    white-space: pre-wrap;
    font-size: 12px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.4);
    width: 240px;
    min-height: 72px;
    max-height: 96px;
    overflow: hidden;
    line-height: 1.45;
  }
  .react-flow__controls { background: rgba(6,13,26,0.9); border: 1px solid rgba(74,163,255,0.18); border-radius: 10px; }
  .react-flow__controls-button { background: transparent; border-color: rgba(74,163,255,0.15); color: var(--ws-text-muted, #5a7a9a); }
  .react-flow__controls-button:hover { background: rgba(74,163,255,0.1); color: var(--ws-text, #ddeeff); }
`;

interface LineageNode {
  id: string;
  label: string;
  prov_type: string;
}

interface LineageEdge {
  id: string;
  source: string;
  target: string;
  label: string;
}

interface LineagePayload {
  nodes: LineageNode[];
  edges: LineageEdge[];
}

const NODE_ROW_GAP = 118;
const MAX_COLUMNS_PER_DEPTH = 4;

function compactLabel(label: string, id: string) {
  const normalized = (label || id).replace(/\s+/g, " ").trim();
  return normalized.length > 110 ? `${normalized.slice(0, 107)}...` : normalized;
}

function buildLineageLayout(payload: LineagePayload, rootId: string, maxDepth: number) {
  const nodeMap = new Map(payload.nodes.map((node) => [node.id, node]));
  const adjacency = new Map<string, Set<string>>();
  payload.nodes.forEach((node) => adjacency.set(node.id, new Set()));
  payload.edges.forEach((edge) => {
    adjacency.get(edge.source)?.add(edge.target);
    adjacency.get(edge.target)?.add(edge.source);
  });

  const depthById = new Map<string, number>([[rootId, 0]]);
  const queue = [rootId];
  while (queue.length > 0) {
    const current = queue.shift();
    if (!current) continue;
    const depth = depthById.get(current) ?? 0;
    if (depth >= maxDepth) continue;
    [...(adjacency.get(current) ?? [])]
      .sort((left, right) => left.localeCompare(right))
      .forEach((neighbor) => {
        if (!depthById.has(neighbor)) {
          depthById.set(neighbor, depth + 1);
          queue.push(neighbor);
        }
      });
  }

  const nodesByDepth = new Map<number, LineageNode[]>();
  depthById.forEach((depth, nodeId) => {
    const node = nodeMap.get(nodeId);
    if (!node) return;
    const level = nodesByDepth.get(depth) ?? [];
    level.push(node);
    nodesByDepth.set(depth, level);
  });

  let levelStartX = 0;
  const mappedNodes = [...nodesByDepth.entries()]
    .sort(([leftDepth], [rightDepth]) => leftDepth - rightDepth)
    .flatMap(([, levelNodes]) => {
    const sorted = [...levelNodes].sort((left, right) => left.label.localeCompare(right.label));
    const columns = Math.min(MAX_COLUMNS_PER_DEPTH, Math.max(1, Math.ceil(Math.sqrt(sorted.length))));
    const rows = Math.ceil(sorted.length / columns);
    const baseX = levelStartX;
    levelStartX += columns * 270 + 80;
    return sorted.map((node, index) => {
      const column = index % columns;
      const row = Math.floor(index / columns);
      return {
        id: node.id,
        data: { label: `${compactLabel(node.label, node.id)}\n(${node.prov_type})` },
        position: {
          x: baseX + column * 270,
          y: (row - (rows - 1) / 2) * NODE_ROW_GAP,
        },
        type: "default",
        style: node.id === rootId
          ? { borderColor: "#4cc38a", boxShadow: "0 0 0 2px rgba(76,195,138,0.18), 0 6px 20px rgba(0,0,0,0.45)" }
          : undefined,
      };
    });
  });

  const visibleIds = new Set(mappedNodes.map((node) => node.id));
  const showEdgeLabels = visibleIds.size <= 40;
  const mappedEdges = payload.edges
    .filter((edge) => visibleIds.has(edge.source) && visibleIds.has(edge.target))
    .map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: showEdgeLabels ? edge.label : undefined,
      animated: false,
      style: { stroke: "#58a6ff", strokeOpacity: 0.65 },
      labelStyle: { fill: "#8fa8c6", fontSize: 10 },
    }));

  return { nodes: mappedNodes, edges: mappedEdges };
}

export function LineageDiagram() {
  const [nodes, setNodes] = useState<any[]>([]);
  const [edges, setEdges] = useState<any[]>([]);
  const [searchId, setSearchId] = useState("");
  const [activeId, setActiveId] = useState("");
  const [error, setError] = useState("");
  const [maxDepth, setMaxDepth] = useState(1);
  const [payload, setPayload] = useState<LineagePayload>({ nodes: [], edges: [] });

  const downloadReport = async (format: "json" | "markdown") => {
    if (!activeId) return;
    const response = await fetch(`/api/provenance/report?node_id=${encodeURIComponent(activeId)}&format=${format}`);
    if (!response.ok) {
      return;
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${activeId}_provenance.${format === "markdown" ? "md" : "json"}`;
    document.body.appendChild(anchor);
    anchor.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(anchor);
  };

  const [prevActiveId, setPrevActiveId] = useState(activeId);
  if (activeId !== prevActiveId) {
    setPrevActiveId(activeId);
    setError("");
    setNodes([]);
    setEdges([]);
    setPayload({ nodes: [], edges: [] });
  }

  const visibleSummary = useMemo(
    () => `${nodes.length} / ${payload.nodes.length} nodes`,
    [nodes.length, payload.nodes.length],
  );

  useEffect(() => {
    let ignore = false;
    if (!activeId) return;

    const fetchLineage = async () => {
      setError("");
      try {
        const res = await fetch("/api/provenance?node_id=" + encodeURIComponent(activeId));

        if (!res.ok) {
          const text = await res.text();
          throw new Error(`HTTP ${res.status}: API Route missing or failed. ${text.substring(0, 100)}`);
        }

        const contentType = res.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
          throw new Error("Backend returned non-JSON response (likely an HTML fallback).");
        }

        const data = await res.json();
        if (res.status === 207) {
          setError(data.message || "Warning: Partial success loading lineage.");
        }

        const nextPayload = data as LineagePayload;
        const layout = buildLineageLayout(nextPayload, activeId, maxDepth);

        if (!ignore) {
          setPayload(nextPayload);
          setNodes(layout.nodes);
          setEdges(layout.edges);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load lineage.");
      }
    };
    void fetchLineage();
    return () => { ignore = true; };
  }, [activeId, maxDepth]);

  return (
    <div style={{ width: "100%", height: "100%", position: "relative", background: "var(--ws-bg, #060d1a)" }}>
      <style>{THEME_CSS}</style>

      {/* Toolbar */}
      <div style={{ position: "absolute", top: 14, left: 14, right: 14, zIndex: 10, display: "flex", gap: 8, alignItems: "center", background: "rgba(4,10,18,0.88)", backdropFilter: "blur(14px)", padding: "8px 12px", borderRadius: 12, border: "1px solid rgba(74,163,255,0.16)", boxShadow: "0 4px 20px rgba(0,0,0,0.4)" }}>
        <span className="ws-eyebrow" style={{ color: "var(--ws-accent, #4aa3ff)", marginRight: 4 }}>PROV-O Lineage</span>
        <input
          className="ws-input"
          type="text"
          placeholder="Enter Node ID…"
          value={searchId}
          onChange={(e) => setSearchId(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") setActiveId(searchId); }}
          style={{ width: 200, padding: "6px 10px", fontSize: 12 }}
        />
        <button className="ws-btn ws-btn--primary" style={{ padding: "6px 12px" }} onClick={() => setActiveId(searchId)}>
          Trace
        </button>
        <div style={{ display: "flex", border: "1px solid var(--ws-border)", borderRadius: 7, overflow: "hidden" }}>
          {[1, 2].map((depth) => (
            <button
              key={depth}
              className="ws-btn ws-btn--ghost"
              style={{ border: 0, borderRadius: 0, padding: "6px 10px", background: maxDepth === depth ? "var(--ws-accent-soft)" : "transparent", color: maxDepth === depth ? "var(--ws-accent)" : "var(--ws-text-dim)" }}
              onClick={() => setMaxDepth(depth)}
              title={`显示 ${depth} 层关系`}
            >
              {depth} hop
            </button>
          ))}
        </div>
        {activeId && payload.nodes.length > 0 && <span className="ws-pill ws-pill--mono">{visibleSummary}</span>}
        <div style={{ flex: 1 }} />
        <button className="ws-btn ws-btn--ghost" style={{ padding: "6px 12px", fontSize: 11 }} disabled={!activeId} onClick={() => void downloadReport("json")}>
          Export JSON
        </button>
        <button className="ws-btn ws-btn--ghost" style={{ padding: "6px 12px", fontSize: 11 }} disabled={!activeId} onClick={() => void downloadReport("markdown")}>
          Export MD
        </button>
      </div>

      {error ? (
        <div style={{ position: "absolute", top: 60, left: 14, right: 14, zIndex: 10, padding: 12, borderRadius: 14, color: "#ffb4c2", background: "rgba(255,157,175,0.1)", border: "1px solid rgba(255,157,175,0.18)" }}>
          {error}
        </div>
      ) : null}

      {activeId ? (
        <ReactFlow key={`${activeId}-${maxDepth}-${nodes.length}`} nodes={nodes} edges={edges} fitView fitViewOptions={{ padding: 0.22, maxZoom: 1.1 }} minZoom={0.1} nodesConnectable={false} nodesDraggable>
          <Background color="rgba(74,163,255,0.08)" gap={24} />
          <Controls />
        </ReactFlow>
      ) : (
        <div className="ws-empty" style={{ height: "100%", paddingTop: 72 }}>
          <div className="ws-empty-icon"><Link2 size={36} color="var(--ws-accent)" /></div>
          <div className="ws-empty-title">PROV-O Lineage Viewer</div>
          <div className="ws-empty-body">Enter a Node ID in the toolbar above and click Trace to view its W3C PROV-O lineage diagram.</div>
        </div>
      )}
    </div>
  );
}
