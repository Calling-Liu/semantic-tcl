import type { GraphLoadPhase, GraphLoadProgress, GraphLoadProgressKind, GraphLayoutSource, GraphLayoutState } from "./types";
import { translate } from "../../i18n";

export const GRAPH_LOAD_STAGE_SEQUENCE: Exclude<GraphLoadPhase, "ready">[] = [
  "bootstrapping",
  "fetching_nodes",
  "fetching_edges",
  "computing_styling",
  "hydrating_scene",
  "stabilizing_layout",
];

export function getGraphLoadTitle(phase: GraphLoadPhase): string {
  switch (phase) {
    case "bootstrapping":
      return translate("Preparing graph session");
    case "fetching_nodes":
      return translate("Loading nodes");
    case "fetching_edges":
      return translate("Loading relationships");
    case "computing_styling":
      return translate("Computing node styling");
    case "hydrating_scene":
      return translate("Hydrating graph scene");
    case "stabilizing_layout":
      return translate("Stabilizing layout");
    case "ready":
    default:
      return translate("Graph ready");
  }
}

export function getGraphLoadStageLabel(phase: Exclude<GraphLoadPhase, "ready">): string {
  switch (phase) {
    case "bootstrapping":
      return translate("Prepare");
    case "fetching_nodes":
      return translate("Nodes");
    case "fetching_edges":
      return translate("Relations");
    case "computing_styling":
      return translate("Styling");
    case "hydrating_scene":
      return translate("Scene");
    case "stabilizing_layout":
      return "Layout";
    default:
      return translate("Stage");
  }
}

export function createGraphLoadProgress(input: {
  phase: GraphLoadPhase;
  message: string;
  progressKind: GraphLoadProgressKind;
  loaded?: number | null;
  total?: number | null;
  nodesLoaded?: number;
  nodesTotal?: number | null;
  edgesLoaded?: number;
  edgesTotal?: number | null;
  showGraphBehind?: boolean;
  layoutSource?: GraphLayoutSource;
  layoutState?: GraphLayoutState;
}): GraphLoadProgress {
  const phaseIndex = GRAPH_LOAD_STAGE_SEQUENCE.indexOf(input.phase as Exclude<GraphLoadPhase, "ready">);

  return {
    phase: input.phase,
    title: getGraphLoadTitle(input.phase),
    message: input.message,
    progressKind: input.progressKind,
    loaded: input.loaded ?? null,
    total: input.total ?? null,
    nodesLoaded: input.nodesLoaded ?? 0,
    nodesTotal: input.nodesTotal ?? null,
    edgesLoaded: input.edgesLoaded ?? 0,
    edgesTotal: input.edgesTotal ?? null,
    showGraphBehind: input.showGraphBehind ?? false,
    stageIndex: phaseIndex >= 0 ? phaseIndex + 1 : GRAPH_LOAD_STAGE_SEQUENCE.length,
    stageCount: GRAPH_LOAD_STAGE_SEQUENCE.length,
    layoutSource: input.layoutSource,
    layoutState: input.layoutState,
  };
}
