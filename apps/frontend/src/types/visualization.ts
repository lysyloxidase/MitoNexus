import type {
  GraphEdge,
  GraphNode,
  KnowledgeGraphData,
  ReportVisualizationPayload,
} from "@mitonexus/shared-types";

export type { GraphEdge, GraphNode, KnowledgeGraphData, ReportVisualizationPayload };

export type ForceGraphNode = GraphNode & {
  x?: number;
  y?: number;
  z?: number;
  fx?: number;
  fy?: number;
  fz?: number;
};
