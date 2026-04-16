import * as THREE from "three";
import { describe, expect, it } from "vitest";

import type { GraphEdge, GraphNode } from "@mitonexus/shared-types";

import {
  LARGE_GRAPH_NODE_THRESHOLD,
  buildForceGraphData,
  buildGraphHighlight,
  findGraphNodeId,
  getEdgeKey,
  shouldUseLightweightRendering,
} from "@/components/3d/ForceGraph";

describe("ForceGraph helpers", () => {
  it("maps empty datasets without crashing", () => {
    expect(buildForceGraphData([], [], null)).toEqual({ nodes: [], links: [] });
  });

  it("switches to lightweight rendering for large datasets", () => {
    expect(shouldUseLightweightRendering(LARGE_GRAPH_NODE_THRESHOLD + 1)).toBe(true);
    expect(shouldUseLightweightRendering(LARGE_GRAPH_NODE_THRESHOLD)).toBe(false);
  });

  it("walks up the object tree to resolve clicked graph nodes", () => {
    const parent = new THREE.Group() as THREE.Group & {
      __graphObjType?: string;
      __data?: { id?: string };
    };
    parent.__graphObjType = "node";
    parent.__data = { id: "therapy:mitoq" };

    const child = new THREE.Mesh(new THREE.SphereGeometry(1), new THREE.MeshBasicMaterial());
    parent.add(child);

    expect(findGraphNodeId(child)).toBe("therapy:mitoq");
  });

  it("builds a focused marker subgraph across gene, cascade, therapy, and pathway nodes", () => {
    const nodes: GraphNode[] = [
      {
        id: "marker:homocysteine",
        type: "marker",
        label: "Homocysteine",
        centrality: 0.8,
        color: "#ef4444",
        size: 12,
        abnormal: true,
        metadata: {},
      },
      {
        id: "gene:mthfr",
        type: "gene",
        label: "MTHFR",
        centrality: 0.6,
        color: "#3b82f6",
        size: 10,
        abnormal: true,
        metadata: {},
      },
      {
        id: "cascade:nrf2_keap1",
        type: "cascade",
        label: "Nrf2/Keap1",
        centrality: 0.7,
        color: "#22c55e",
        size: 14,
        abnormal: true,
        metadata: {},
      },
      {
        id: "therapy:mitoq",
        type: "therapy",
        label: "MitoQ",
        centrality: 0.55,
        color: "#a855f7",
        size: 13,
        abnormal: false,
        metadata: {},
      },
      {
        id: "pathway:hsa00190",
        type: "pathway",
        label: "OXPHOS",
        centrality: 0.5,
        color: "#f59e0b",
        size: 11,
        abnormal: false,
        metadata: {},
      },
      {
        id: "marker:glucose",
        type: "marker",
        label: "Glucose",
        centrality: 0.4,
        color: "#ef4444",
        size: 11,
        abnormal: false,
        metadata: {},
      },
    ];

    const edges: GraphEdge[] = [
      {
        source: "marker:homocysteine",
        target: "gene:mthfr",
        type: "regulation",
        confidence: 0.8,
        color: "#3b82f6",
        width: 1.4,
      },
      {
        source: "gene:mthfr",
        target: "cascade:nrf2_keap1",
        type: "activation",
        confidence: 0.7,
        color: "#22c55e",
        width: 1.5,
      },
      {
        source: "therapy:mitoq",
        target: "cascade:nrf2_keap1",
        type: "treats",
        confidence: 0.8,
        color: "#a855f7",
        width: 1.7,
      },
      {
        source: "cascade:nrf2_keap1",
        target: "pathway:hsa00190",
        type: "correlation",
        confidence: 0.6,
        color: "#94a3b8",
        width: 1.2,
      },
      {
        source: "marker:glucose",
        target: "cascade:nrf2_keap1",
        type: "regulation",
        confidence: 0.5,
        color: "#3b82f6",
        width: 1.1,
      },
    ];

    const highlight = buildGraphHighlight("marker:homocysteine", [...nodes], edges);

    expect(highlight.nodeIds).toEqual(
      new Set([
        "marker:homocysteine",
        "gene:mthfr",
        "cascade:nrf2_keap1",
        "therapy:mitoq",
        "pathway:hsa00190",
      ]),
    );
    expect(highlight.nodeIds.has("marker:glucose")).toBe(false);
    expect(highlight.edgeIds.has(getEdgeKey(edges[0]))).toBe(true);
    expect(highlight.edgeIds.has(getEdgeKey(edges[1]))).toBe(true);
    expect(highlight.edgeIds.has(getEdgeKey(edges[2]))).toBe(true);
    expect(highlight.edgeIds.has(getEdgeKey(edges[3]))).toBe(true);
    expect(highlight.edgeIds.has(getEdgeKey(edges[4]))).toBe(false);
  });
});
