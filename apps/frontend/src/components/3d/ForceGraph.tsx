"use client";

import type {
  GraphEdge,
  GraphNode,
  GraphNodeType,
  KnowledgeGraphData,
} from "@mitonexus/shared-types";
import { useFrame } from "@react-three/fiber";
import type { ThreeEvent } from "@react-three/fiber";
import { memo, useEffect, useMemo } from "react";
import * as THREE from "three";
import ThreeForceGraph from "three-forcegraph";

import { EDGE_COLOR_MAP, NODE_COLOR_MAP } from "@/lib/graph-styling";
import type { ForceGraphNode } from "@/types/visualization";

type ForceGraphProps = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  positions?: KnowledgeGraphData["precomputed_positions"];
  onNodeClick: (nodeId: string) => void;
  selectedNodeId?: string | null;
  patientTargetedNodeIds?: Set<string>;
};

type GraphDataShape = {
  nodes: ForceGraphNode[];
  links: GraphEdge[];
};

type GraphLinkLike = Omit<GraphEdge, "source" | "target"> & {
  source: string | { id?: string };
  target: string | { id?: string };
};

type GraphHighlight = {
  nodeIds: Set<string>;
  edgeIds: Set<string>;
};

type GraphObjectTarget = THREE.Object3D & {
  __graphObjType?: string;
  __data?: { id?: string };
};

const SHARED_GEOMETRIES = {
  marker: new THREE.TetrahedronGeometry(1, 0),
  gene: new THREE.SphereGeometry(1, 12, 12),
  cascade: new THREE.OctahedronGeometry(1, 0),
  therapy: new THREE.BoxGeometry(1, 1, 1),
  pathway: new THREE.IcosahedronGeometry(1, 0),
} as const;

export const LARGE_GRAPH_NODE_THRESHOLD = 500;

export function shouldUseLightweightRendering(nodeCount: number): boolean {
  return nodeCount > LARGE_GRAPH_NODE_THRESHOLD;
}

export function buildForceGraphData(
  nodes: GraphNode[],
  edges: GraphEdge[],
  positions?: KnowledgeGraphData["precomputed_positions"],
): GraphDataShape {
  return {
    nodes: nodes.map((node) => {
      const position = positions?.[node.id];
      if (!position) {
        return { ...node };
      }

      return {
        ...node,
        x: position[0],
        y: position[1],
        z: position[2],
        fx: position[0],
        fy: position[1],
        fz: position[2],
      };
    }),
    links: edges.map((edge) => ({
      ...edge,
      source: readLinkedNodeId(edge.source) ?? edge.source,
      target: readLinkedNodeId(edge.target) ?? edge.target,
    })),
  };
}

export function findGraphNodeId(target: THREE.Object3D | null): string | null {
  let current: GraphObjectTarget | null = target as GraphObjectTarget | null;

  while (current) {
    if (current.__graphObjType === "node" && typeof current.__data?.id === "string") {
      return current.__data.id;
    }
    current = current.parent as GraphObjectTarget | null;
  }

  return null;
}

export function getEdgeKey(edge: GraphLinkLike): string {
  const sourceId = readLinkedNodeId(edge.source);
  const targetId = readLinkedNodeId(edge.target);
  return `${sourceId ?? "unknown"}|${targetId ?? "unknown"}|${edge.type}`;
}

export function buildGraphHighlight(
  selectedNodeId: string | null | undefined,
  nodes: GraphNode[],
  edges: GraphEdge[],
): GraphHighlight {
  if (!selectedNodeId) {
    return { nodeIds: new Set<string>(), edgeIds: new Set<string>() };
  }

  const selectedNode = nodes.find((node) => node.id === selectedNodeId);
  if (!selectedNode) {
    return { nodeIds: new Set<string>(), edgeIds: new Set<string>() };
  }

  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const adjacency = buildAdjacency(edges);
  const highlightedNodeIds = new Set<string>([selectedNodeId]);

  const addGroup = (nodeIds: Iterable<string>) => {
    for (const nodeId of nodeIds) {
      highlightedNodeIds.add(nodeId);
    }
  };

  switch (selectedNode.type) {
    case "marker": {
      const genes = collectNeighborsByType([selectedNodeId], adjacency, nodeById, ["gene"]);
      const directCascades = collectNeighborsByType([selectedNodeId], adjacency, nodeById, [
        "cascade",
      ]);
      const cascades = new Set<string>([
        ...directCascades,
        ...collectNeighborsByType(genes, adjacency, nodeById, ["cascade"]),
      ]);
      const pathways = new Set<string>([
        ...collectNeighborsByType([selectedNodeId], adjacency, nodeById, ["pathway"]),
        ...collectNeighborsByType(cascades, adjacency, nodeById, ["pathway"]),
      ]);
      const therapies = collectNeighborsByType(cascades, adjacency, nodeById, ["therapy"]);

      addGroup(genes);
      addGroup(cascades);
      addGroup(pathways);
      addGroup(therapies);
      break;
    }
    case "gene": {
      const markers = collectNeighborsByType([selectedNodeId], adjacency, nodeById, ["marker"]);
      const cascades = collectNeighborsByType([selectedNodeId], adjacency, nodeById, ["cascade"]);
      const therapies = collectNeighborsByType(cascades, adjacency, nodeById, ["therapy"]);
      const pathways = new Set<string>([
        ...collectNeighborsByType(cascades, adjacency, nodeById, ["pathway"]),
        ...collectNeighborsByType(markers, adjacency, nodeById, ["pathway"]),
      ]);

      addGroup(markers);
      addGroup(cascades);
      addGroup(pathways);
      addGroup(therapies);
      break;
    }
    case "cascade": {
      addGroup(collectNeighborsByType([selectedNodeId], adjacency, nodeById, ["marker"]));
      addGroup(collectNeighborsByType([selectedNodeId], adjacency, nodeById, ["gene"]));
      addGroup(collectNeighborsByType([selectedNodeId], adjacency, nodeById, ["therapy"]));
      addGroup(collectNeighborsByType([selectedNodeId], adjacency, nodeById, ["pathway"]));
      break;
    }
    case "therapy": {
      const cascades = collectNeighborsByType([selectedNodeId], adjacency, nodeById, ["cascade"]);
      addGroup(cascades);
      addGroup(collectNeighborsByType(cascades, adjacency, nodeById, ["gene", "pathway"]));
      addGroup(collectNeighborsByType(cascades, adjacency, nodeById, ["marker"]));
      break;
    }
    case "pathway": {
      const cascades = collectNeighborsByType([selectedNodeId], adjacency, nodeById, ["cascade"]);
      const markers = collectNeighborsByType([selectedNodeId], adjacency, nodeById, ["marker"]);
      addGroup(cascades);
      addGroup(markers);
      addGroup(collectNeighborsByType(cascades, adjacency, nodeById, ["gene", "therapy"]));
      addGroup(collectNeighborsByType(markers, adjacency, nodeById, ["gene"]));
      break;
    }
  }

  const edgeIds = new Set(
    edges
      .filter(
        (edge) =>
          highlightedNodeIds.has(readLinkedNodeId(edge.source) ?? "") &&
          highlightedNodeIds.has(readLinkedNodeId(edge.target) ?? ""),
      )
      .map((edge) => getEdgeKey(edge)),
  );

  return { nodeIds: highlightedNodeIds, edgeIds };
}

function ForceGraphComponent({
  nodes,
  edges,
  positions,
  onNodeClick,
  selectedNodeId = null,
  patientTargetedNodeIds = new Set<string>(),
}: ForceGraphProps) {
  const lightweightMode = shouldUseLightweightRendering(nodes.length);
  const graphData = useMemo(
    () => buildForceGraphData(nodes, edges, positions),
    [edges, nodes, positions],
  );
  const highlight = useMemo(
    () => buildGraphHighlight(selectedNodeId, nodes, edges),
    [edges, nodes, selectedNodeId],
  );
  const hasSelection = Boolean(selectedNodeId && highlight.nodeIds.size > 0);
  const hasPatientTargets = patientTargetedNodeIds.size > 0;
  const graph = useMemo(() => new ThreeForceGraph<ForceGraphNode, GraphEdge>(), []);

  useEffect(() => {
    graph
      .numDimensions(3)
      .nodeId("id")
      .graphData(graphData)
      .nodeOpacity(1)
      .nodeResolution(lightweightMode ? 6 : 12)
      .nodeVal((node) => Math.max(node.size * 1.18, 1.4))
      .nodeColor((node) => NODE_COLOR_MAP[node.type] ?? node.color)
      .linkColor((edge) => {
        const sourceId = readLinkedNodeId(edge.source);
        const targetId = readLinkedNodeId(edge.target);

        if (hasSelection && !highlight.edgeIds.has(getEdgeKey(edge))) {
          return "#334155";
        }

        if (
          !hasSelection &&
          hasPatientTargets &&
          (!sourceId ||
            !targetId ||
            (!patientTargetedNodeIds.has(sourceId) && !patientTargetedNodeIds.has(targetId)))
        ) {
          return "#334155";
        }

        return EDGE_COLOR_MAP[edge.type] ?? edge.color;
      })
      .linkVisibility((edge) => {
        if (hasSelection) {
          return highlight.edgeIds.has(getEdgeKey(edge));
        }
        return true;
      })
      .linkOpacity(hasSelection ? 0.9 : hasPatientTargets ? 0.82 : 0.68)
      .linkWidth((edge) =>
        hasSelection
          ? highlight.edgeIds.has(getEdgeKey(edge))
            ? Math.max(edge.width * 2.4, 2.8)
            : 0
          : Math.max(
              edge.width *
                (hasPatientTargets && isPatientTargetEdge(edge, patientTargetedNodeIds)
                  ? 2.1
                  : 1.3),
              hasPatientTargets && isPatientTargetEdge(edge, patientTargetedNodeIds) ? 2.2 : 1.2,
            ),
      )
      .linkDirectionalParticles((edge) => {
        if (hasSelection && !highlight.edgeIds.has(getEdgeKey(edge))) {
          return 0;
        }
        if (lightweightMode) {
          return 0;
        }
        return edge.type === "activation" || edge.type === "inhibition" ? 6 : 2;
      })
      .linkDirectionalParticleSpeed((edge) =>
        lightweightMode ? 0 : Math.max(edge.confidence * 0.012, 0.004),
      )
      .linkDirectionalParticleWidth((edge) =>
        lightweightMode ? 0 : Math.max(edge.width * 1.1, 1.2),
      )
      .cooldownTicks(graphData.nodes.some((node) => node.fx !== undefined) ? 0 : 120)
      .d3VelocityDecay(0.18)
      .d3AlphaDecay(0.035)
      .nodePositionUpdate((object, coords) => {
        object.position.set(coords.x, coords.y, coords.z);
        return true;
      });

    if (lightweightMode) {
      graph.nodeThreeObject((node) =>
        createLightweightNodeMesh(
          node,
          resolveNodeVisualState(
            node.id,
            selectedNodeId,
            highlight.nodeIds,
            patientTargetedNodeIds,
          ),
        ),
      );
      return;
    }

    graph.nodeThreeObject((node) =>
      createNodeMesh(
        node,
        resolveNodeVisualState(node.id, selectedNodeId, highlight.nodeIds, patientTargetedNodeIds),
      ),
    );
  }, [
    graph,
    graphData,
    hasSelection,
    hasPatientTargets,
    highlight.edgeIds,
    highlight.nodeIds,
    lightweightMode,
    patientTargetedNodeIds,
    selectedNodeId,
  ]);

  useEffect(() => {
    return () => {
      const destroyable = graph as typeof graph & { _destructor?: () => void };
      destroyable._destructor?.();
    };
  }, [graph]);

  useFrame(() => {
    graph.tickFrame();
  });

  const handleNodeClick = (event: ThreeEvent<PointerEvent>) => {
    const nodeId = findGraphNodeId(event.object);
    if (nodeId) {
      onNodeClick(nodeId);
    }
  };

  return <primitive object={graph} onPointerDown={handleNodeClick} />;
}

export const ForceGraph = memo(ForceGraphComponent);

function createNodeMesh(node: GraphNode, visualState: NodeVisualState): THREE.Object3D {
  const opacity = resolveNodeOpacity(visualState);
  const material = new THREE.MeshStandardMaterial({
    color: resolveNodeColor(node.color, visualState),
    emissive: resolveNodeEmissive(node, visualState),
    emissiveIntensity: resolveNodeEmissiveIntensity(node, visualState),
    metalness: visualState === "selected" ? 0.12 : 0.18,
    opacity,
    roughness: visualState === "selected" ? 0.28 : 0.42,
    transparent: opacity < 1,
  });

  const geometry = SHARED_GEOMETRIES[node.type];
  const mesh = new THREE.Mesh(geometry, material);
  const scale = resolveNodeScale(node.size, visualState, 8.6, 1.05);
  mesh.scale.setScalar(scale);
  mesh.renderOrder = visualState === "selected" ? 10 : 0;
  return mesh;
}

function createLightweightNodeMesh(node: GraphNode, visualState: NodeVisualState): THREE.Object3D {
  const opacity = resolveNodeOpacity(visualState);
  const material = new THREE.MeshStandardMaterial({
    color: resolveNodeColor(node.color, visualState),
    emissive: resolveNodeEmissive(node, visualState),
    emissiveIntensity: resolveNodeEmissiveIntensity(node, visualState),
    metalness: 0.08,
    opacity,
    roughness: 0.7,
    transparent: opacity < 1,
  });

  const mesh = new THREE.Mesh(SHARED_GEOMETRIES.gene, material);
  const scale = resolveNodeScale(node.size, visualState, 9.8, 0.9);
  mesh.scale.setScalar(scale);
  mesh.renderOrder = visualState === "selected" ? 10 : 0;
  return mesh;
}

type NodeVisualState = "default" | "selected" | "related" | "targeted" | "context" | "dimmed";

function buildAdjacency(edges: GraphEdge[]): Map<string, GraphEdge[]> {
  const adjacency = new Map<string, GraphEdge[]>();
  for (const edge of edges) {
    adjacency.set(edge.source, [...(adjacency.get(edge.source) ?? []), edge]);
    adjacency.set(edge.target, [...(adjacency.get(edge.target) ?? []), edge]);
  }
  return adjacency;
}

function collectNeighborsByType(
  sourceIds: Iterable<string>,
  adjacency: Map<string, GraphEdge[]>,
  nodeById: Map<string, GraphNode>,
  allowedTypes: GraphNodeType[],
): Set<string> {
  const allowed = new Set(allowedTypes);
  const collected = new Set<string>();

  for (const sourceId of sourceIds) {
    for (const edge of adjacency.get(sourceId) ?? []) {
      const neighborId = edge.source === sourceId ? edge.target : edge.source;
      const neighbor = nodeById.get(neighborId);
      if (neighbor && allowed.has(neighbor.type)) {
        collected.add(neighborId);
      }
    }
  }

  return collected;
}

function readLinkedNodeId(value: string | { id?: string }): string | null {
  if (typeof value === "string") {
    return value;
  }
  if (typeof value?.id === "string") {
    return value.id;
  }
  return null;
}

function resolveNodeVisualState(
  nodeId: string,
  selectedNodeId: string | null,
  highlightedNodeIds: Set<string>,
  patientTargetedNodeIds: Set<string>,
): NodeVisualState {
  if (!selectedNodeId || highlightedNodeIds.size === 0) {
    if (patientTargetedNodeIds.size === 0) {
      return "default";
    }
    return patientTargetedNodeIds.has(nodeId) ? "targeted" : "context";
  }
  if (nodeId === selectedNodeId) {
    return "selected";
  }
  if (highlightedNodeIds.has(nodeId)) {
    return "related";
  }
  return "dimmed";
}

function resolveNodeColor(color: string, visualState: NodeVisualState): THREE.ColorRepresentation {
  const baseColor = new THREE.Color(color);
  if (visualState === "dimmed") {
    return baseColor.lerp(new THREE.Color("#0f172a"), 0.76);
  }
  if (visualState === "selected") {
    return baseColor.lerp(new THREE.Color("#ffffff"), 0.18);
  }
  if (visualState === "related") {
    return baseColor.lerp(new THREE.Color("#f8fafc"), 0.08);
  }
  if (visualState === "targeted") {
    return baseColor.lerp(new THREE.Color("#ffffff"), 0.12);
  }
  if (visualState === "context") {
    return baseColor.lerp(new THREE.Color("#0f172a"), 0.58);
  }
  return baseColor;
}

function resolveNodeEmissive(node: GraphNode, visualState: NodeVisualState): THREE.Color {
  if (visualState === "selected") {
    return new THREE.Color("#ffffff");
  }
  if (node.abnormal) {
    return new THREE.Color("#fb7185");
  }
  return new THREE.Color(node.color);
}

function resolveNodeEmissiveIntensity(node: GraphNode, visualState: NodeVisualState): number {
  if (visualState === "selected") {
    return 0.88;
  }
  if (visualState === "related") {
    return node.abnormal ? 0.55 : 0.34;
  }
  if (visualState === "targeted") {
    return node.abnormal ? 0.62 : 0.44;
  }
  if (visualState === "context") {
    return 0.08;
  }
  if (visualState === "dimmed") {
    return 0.03;
  }
  return node.abnormal ? 0.34 : 0.16;
}

function resolveNodeOpacity(visualState: NodeVisualState): number {
  if (visualState === "selected") {
    return 1;
  }
  if (visualState === "related") {
    return 0.98;
  }
  if (visualState === "targeted") {
    return 1;
  }
  if (visualState === "context") {
    return 0.36;
  }
  if (visualState === "dimmed") {
    return 0.12;
  }
  return 0.96;
}

function resolveNodeScale(
  size: number,
  visualState: NodeVisualState,
  divisor: number,
  fallback: number,
): number {
  const base = Math.max(size / divisor, fallback);
  if (visualState === "selected") {
    return base * 1.42;
  }
  if (visualState === "related") {
    return base * 1.14;
  }
  if (visualState === "targeted") {
    return base * 1.12;
  }
  if (visualState === "context") {
    return base * 0.92;
  }
  if (visualState === "dimmed") {
    return base * 0.82;
  }
  return base;
}

function isPatientTargetEdge(edge: GraphLinkLike, patientTargetedNodeIds: Set<string>): boolean {
  const sourceId = readLinkedNodeId(edge.source);
  const targetId = readLinkedNodeId(edge.target);

  if (!sourceId || !targetId) {
    return false;
  }

  return patientTargetedNodeIds.has(sourceId) && patientTargetedNodeIds.has(targetId);
}
