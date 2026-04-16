"use client";

import type { GraphEdge, GraphNode, KnowledgeGraphData } from "@mitonexus/shared-types";
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
};

type GraphDataShape = {
  nodes: ForceGraphNode[];
  links: GraphEdge[];
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
    links: edges,
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

function ForceGraphComponent({ nodes, edges, positions, onNodeClick }: ForceGraphProps) {
  const lightweightMode = shouldUseLightweightRendering(nodes.length);
  const graphData = useMemo(
    () => buildForceGraphData(nodes, edges, positions),
    [edges, nodes, positions],
  );
  const graph = useMemo(() => new ThreeForceGraph<ForceGraphNode, GraphEdge>(), []);

  useEffect(() => {
    graph
      .numDimensions(3)
      .nodeId("id")
      .graphData(graphData)
      .nodeOpacity(0.95)
      .nodeResolution(lightweightMode ? 6 : 12)
      .nodeVal((node) => Math.max(node.size, 1))
      .nodeColor((node) => NODE_COLOR_MAP[node.type] ?? node.color)
      .linkColor((edge) => EDGE_COLOR_MAP[edge.type] ?? edge.color)
      .linkWidth((edge) => edge.width)
      .linkDirectionalParticles((edge) => {
        if (lightweightMode) {
          return 0;
        }
        return edge.type === "activation" || edge.type === "inhibition" ? 4 : 1;
      })
      .linkDirectionalParticleSpeed((edge) => (lightweightMode ? 0 : edge.confidence * 0.01))
      .linkDirectionalParticleWidth((edge) => (lightweightMode ? 0 : edge.width * 0.75))
      .cooldownTicks(graphData.nodes.some((node) => node.fx !== undefined) ? 0 : 120)
      .d3VelocityDecay(0.18)
      .d3AlphaDecay(0.035)
      .nodePositionUpdate((object, coords) => {
        object.position.set(coords.x, coords.y, coords.z);
        return true;
      });

    if (lightweightMode) {
      graph.nodeThreeObject((node) => createLightweightNodeMesh(node));
      return;
    }

    graph.nodeThreeObject((node) => createNodeMesh(node));
  }, [graph, graphData, lightweightMode]);

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

function createNodeMesh(node: GraphNode): THREE.Object3D {
  const material = new THREE.MeshStandardMaterial({
    color: node.color,
    emissive: node.abnormal ? new THREE.Color("#fb7185") : new THREE.Color(node.color),
    emissiveIntensity: node.abnormal ? 0.32 : 0.08,
    metalness: 0.18,
    roughness: 0.42,
  });

  const geometry = SHARED_GEOMETRIES[node.type];
  const mesh = new THREE.Mesh(geometry, material);
  const scale = Math.max(node.size / 10, 0.8);
  mesh.scale.setScalar(scale);
  return mesh;
}

function createLightweightNodeMesh(node: GraphNode): THREE.Object3D {
  const material = new THREE.MeshStandardMaterial({
    color: node.color,
    emissive: node.abnormal ? new THREE.Color("#fb7185") : new THREE.Color(node.color),
    emissiveIntensity: node.abnormal ? 0.22 : 0.06,
    metalness: 0.08,
    roughness: 0.7,
  });

  const mesh = new THREE.Mesh(SHARED_GEOMETRIES.gene, material);
  const scale = Math.max(node.size / 11, 0.75);
  mesh.scale.setScalar(scale);
  return mesh;
}
