import type { GraphEdgeType, GraphNodeType } from "@mitonexus/shared-types";

export const NODE_COLOR_MAP: Record<GraphNodeType, string> = {
  marker: "#ef4444",
  gene: "#3b82f6",
  cascade: "#22c55e",
  therapy: "#a855f7",
  pathway: "#f59e0b",
};

export const EDGE_COLOR_MAP: Record<GraphEdgeType, string> = {
  activation: "#22c55e",
  inhibition: "#ef4444",
  regulation: "#3b82f6",
  correlation: "#94a3b8",
  treats: "#a855f7",
};

export const NODE_LABEL_MAP: Record<GraphNodeType, string> = {
  marker: "Blood marker",
  gene: "Gene",
  cascade: "Cascade",
  therapy: "Therapy",
  pathway: "Pathway",
};

export const EDGE_LABEL_MAP: Record<GraphEdgeType, string> = {
  activation: "Activation",
  inhibition: "Inhibition",
  regulation: "Regulation",
  correlation: "Correlation",
  treats: "Treats",
};
