import { describe, expect, it } from "vitest";

import type { GraphEdge, GraphNode, KnowledgeGraphData } from "@mitonexus/shared-types";

import {
  buildPatientTargetSummary,
  filterGraphToNodeIds,
  getPatientTargetReason,
  getPatientTargetedNodeIds,
} from "@/lib/graph-focus";

describe("graph focus helpers", () => {
  const nodes: GraphNode[] = [
    {
      id: "marker:homocysteine",
      type: "marker",
      label: "Homocysteine",
      centrality: 0.9,
      color: "#ef4444",
      size: 12,
      abnormal: true,
      metadata: { status: "high" },
    },
    {
      id: "marker:hdl",
      type: "marker",
      label: "HDL",
      centrality: 0.3,
      color: "#22c55e",
      size: 10,
      abnormal: false,
      metadata: { status: "optimal" },
    },
    {
      id: "gene:mthfr",
      type: "gene",
      label: "MTHFR",
      centrality: 0.7,
      color: "#3b82f6",
      size: 10,
      abnormal: false,
      metadata: {},
    },
    {
      id: "cascade:nrf2_keap1",
      type: "cascade",
      label: "Nrf2/Keap1",
      centrality: 0.8,
      color: "#22c55e",
      size: 14,
      abnormal: true,
      metadata: { status: "moderately_affected" },
    },
    {
      id: "therapy:mitoq",
      type: "therapy",
      label: "MitoQ",
      centrality: 0.6,
      color: "#a855f7",
      size: 13,
      abnormal: false,
      metadata: {},
    },
    {
      id: "pathway:hsa00190",
      type: "pathway",
      label: "OXPHOS",
      centrality: 0.55,
      color: "#f59e0b",
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
      width: 1.5,
    },
    {
      source: "gene:mthfr",
      target: "cascade:nrf2_keap1",
      type: "activation",
      confidence: 0.75,
      color: "#22c55e",
      width: 1.6,
    },
    {
      source: "therapy:mitoq",
      target: "cascade:nrf2_keap1",
      type: "treats",
      confidence: 0.82,
      color: "#a855f7",
      width: 1.8,
    },
    {
      source: "cascade:nrf2_keap1",
      target: "pathway:hsa00190",
      type: "correlation",
      confidence: 0.64,
      color: "#94a3b8",
      width: 1.2,
    },
    {
      source: "marker:hdl",
      target: "pathway:hsa00190",
      type: "correlation",
      confidence: 0.4,
      color: "#94a3b8",
      width: 1,
    },
  ];

  it("extracts the patient-targeted subgraph", () => {
    const targetedIds = getPatientTargetedNodeIds(nodes, edges);

    expect(targetedIds).toEqual(
      new Set([
        "marker:homocysteine",
        "gene:mthfr",
        "cascade:nrf2_keap1",
        "therapy:mitoq",
        "pathway:hsa00190",
      ]),
    );
    expect(targetedIds.has("marker:hdl")).toBe(false);
  });

  it("filters graph payload to patient-targeted nodes", () => {
    const data: KnowledgeGraphData = {
      nodes,
      edges,
      layout: "hybrid",
      precomputed_positions: {
        "marker:homocysteine": [0, 0, 0],
        "marker:hdl": [1, 1, 1],
        "gene:mthfr": [2, 2, 2],
        "cascade:nrf2_keap1": [3, 3, 3],
        "therapy:mitoq": [4, 4, 4],
        "pathway:hsa00190": [5, 5, 5],
      },
    };

    const targetedIds = getPatientTargetedNodeIds(nodes, edges);
    const filtered = filterGraphToNodeIds(data, targetedIds);

    expect(filtered.nodes.map((node) => node.id)).not.toContain("marker:hdl");
    expect(filtered.edges).toHaveLength(4);
    expect(filtered.precomputed_positions).not.toHaveProperty("marker:hdl");
  });

  it("keeps edges after graph libraries mutate source and target into node refs", () => {
    const data: KnowledgeGraphData = {
      nodes,
      edges: edges.map((edge) => ({
        ...edge,
        source: { id: edge.source },
        target: { id: edge.target },
      })) as unknown as GraphEdge[],
      layout: "hybrid",
      precomputed_positions: null,
    };

    const targetedIds = getPatientTargetedNodeIds(nodes, edges);
    const filtered = filterGraphToNodeIds(data, targetedIds);

    expect(filtered.edges).toHaveLength(4);
  });

  it("groups patient-targeted nodes by type and describes why they matter", () => {
    const targetedIds = getPatientTargetedNodeIds(nodes, edges);
    const summary = buildPatientTargetSummary(nodes, targetedIds);

    expect(summary.marker).toHaveLength(1);
    expect(summary.therapy).toHaveLength(1);
    expect(summary.pathway).toHaveLength(1);
    expect(getPatientTargetReason(nodes[0], targetedIds)).toContain("actionable");
    expect(getPatientTargetReason(nodes[1], targetedIds)).toBeNull();
  });

  it("keeps bridging cascades and genes even when they are not themselves abnormal", () => {
    const bridgeNodes: GraphNode[] = [
      {
        id: "marker:glucose",
        type: "marker",
        label: "Glucose",
        centrality: 0.9,
        color: "#ef4444",
        size: 12,
        abnormal: true,
        metadata: { status: "high" },
      },
      {
        id: "gene:akt1",
        type: "gene",
        label: "AKT1",
        centrality: 0.6,
        color: "#3b82f6",
        size: 10,
        abnormal: false,
        metadata: {},
      },
      {
        id: "cascade:mtorc2",
        type: "cascade",
        label: "mTORC2/AKT",
        centrality: 0.7,
        color: "#22c55e",
        size: 14,
        abnormal: false,
        metadata: { status: "optimal" },
      },
      {
        id: "therapy:berberine",
        type: "therapy",
        label: "Berberine",
        centrality: 0.65,
        color: "#a855f7",
        size: 13,
        abnormal: false,
        metadata: {},
      },
    ];

    const bridgeEdges: GraphEdge[] = [
      {
        source: "marker:glucose",
        target: "gene:akt1",
        type: "regulation",
        confidence: 0.8,
        color: "#3b82f6",
        width: 1.4,
      },
      {
        source: "gene:akt1",
        target: "cascade:mtorc2",
        type: "activation",
        confidence: 0.76,
        color: "#22c55e",
        width: 1.5,
      },
      {
        source: "therapy:berberine",
        target: "cascade:mtorc2",
        type: "treats",
        confidence: 0.78,
        color: "#a855f7",
        width: 1.7,
      },
    ];

    const targetedIds = getPatientTargetedNodeIds(bridgeNodes, bridgeEdges);

    expect(targetedIds).toEqual(
      new Set(["marker:glucose", "gene:akt1", "cascade:mtorc2", "therapy:berberine"]),
    );
  });
});
