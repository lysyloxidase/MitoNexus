"use client";

import type { KnowledgeGraphData } from "@mitonexus/shared-types";
import { OrbitControls, PerspectiveCamera, Stats } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { Bloom, EffectComposer, SSAO } from "@react-three/postprocessing";
import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";

import { ForceGraph, buildGraphHighlight } from "@/components/3d/ForceGraph";
import { GraphControls } from "@/components/3d/GraphControls";
import { GraphLegend } from "@/components/3d/GraphLegend";
import {
  buildPatientTargetSummary,
  filterGraphToNodeIds,
  getPatientTargetReason,
  getPatientTargetedNodeIds,
} from "@/lib/graph-focus";

const NodeDetailPanel = dynamic(
  () => import("./NodeDetailPanel").then((module) => module.NodeDetailPanel),
  { ssr: false },
);

type KnowledgeGraphSceneProps = {
  data: KnowledgeGraphData;
};

export default function KnowledgeGraphScene({ data }: KnowledgeGraphSceneProps) {
  const [viewMode, setViewMode] = useState<"patient" | "full">("patient");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const patientTargetedNodeIds = useMemo(
    () => getPatientTargetedNodeIds(data.nodes, data.edges),
    [data.edges, data.nodes],
  );
  const visibleData = useMemo(
    () => (viewMode === "patient" ? filterGraphToNodeIds(data, patientTargetedNodeIds) : data),
    [data, patientTargetedNodeIds, viewMode],
  );
  const patientTargetSummary = useMemo(
    () => buildPatientTargetSummary(data.nodes, patientTargetedNodeIds),
    [data.nodes, patientTargetedNodeIds],
  );
  const selectedNode = useMemo(
    () => visibleData.nodes.find((node) => node.id === selectedNodeId) ?? null,
    [selectedNodeId, visibleData.nodes],
  );
  const highlight = useMemo(
    () => buildGraphHighlight(selectedNodeId, visibleData.nodes, visibleData.edges),
    [selectedNodeId, visibleData.edges, visibleData.nodes],
  );
  const selectedNodeReason = useMemo(
    () => (selectedNode ? getPatientTargetReason(selectedNode, patientTargetedNodeIds) : null),
    [patientTargetedNodeIds, selectedNode],
  );

  useEffect(() => {
    if (selectedNodeId && !visibleData.nodes.some((node) => node.id === selectedNodeId)) {
      setSelectedNodeId(null);
    }
  }, [selectedNodeId, visibleData.nodes]);

  return (
    <div className="relative h-[calc(100vh-8rem)] w-full overflow-hidden rounded-[2rem] border border-white/10 bg-[radial-gradient(circle_at_top,_rgba(8,145,178,0.18),_transparent_30%),radial-gradient(circle_at_bottom_left,_rgba(249,115,22,0.12),_transparent_30%),linear-gradient(180deg,_#020617_0%,_#0f172a_55%,_#111827_100%)] shadow-[0_36px_120px_-70px_rgba(15,23,42,1)]">
      <Canvas dpr={[1, 2]} onPointerMissed={() => setSelectedNodeId(null)}>
        <PerspectiveCamera fov={46} makeDefault position={[0, 0, 700]} />
        <color args={["#020617"]} attach="background" />
        <fog args={["#020617", 720, 1500]} attach="fog" />

        <ambientLight intensity={0.82} />
        <pointLight intensity={1.45} position={[220, 180, 260]} />
        <pointLight color="#0ea5e9" intensity={1.05} position={[-280, -160, -220]} />
        <pointLight color="#f97316" intensity={0.72} position={[0, -220, 190]} />

        <ForceGraph
          edges={visibleData.edges}
          nodes={visibleData.nodes}
          onNodeClick={setSelectedNodeId}
          patientTargetedNodeIds={patientTargetedNodeIds}
          positions={visibleData.precomputed_positions}
          selectedNodeId={selectedNodeId}
        />

        <OrbitControls
          autoRotate={!selectedNode}
          autoRotateSpeed={0.14}
          dampingFactor={0.06}
          enableDamping
        />

        <EffectComposer enableNormalPass>
          <Bloom intensity={1.15} luminanceSmoothing={0.94} luminanceThreshold={0.28} />
          <SSAO intensity={4.2} radius={0.16} />
        </EffectComposer>

        {process.env.NODE_ENV === "development" ? <Stats /> : null}
      </Canvas>

      <GraphLegend />
      <GraphControls
        edgeCount={visibleData.edges.length}
        layout={visibleData.layout}
        nodeCount={visibleData.nodes.length}
        onViewModeChange={setViewMode}
        patientCounts={{
          cascades: patientTargetSummary.cascade.length,
          genes: patientTargetSummary.gene.length,
          markers: patientTargetSummary.marker.length,
          pathways: patientTargetSummary.pathway.length,
          therapies: patientTargetSummary.therapy.length,
        }}
        selectedNodeLabel={selectedNode?.label ?? null}
        selectedSubgraphEdgeCount={highlight.edgeIds.size}
        selectedSubgraphNodeCount={highlight.nodeIds.size}
        viewMode={viewMode}
      />

      {selectedNode ? (
        <NodeDetailPanel
          isPatientTargeted={patientTargetedNodeIds.has(selectedNode.id)}
          node={selectedNode}
          onClose={() => setSelectedNodeId(null)}
          patientTargetReason={selectedNodeReason}
        />
      ) : null}
    </div>
  );
}
