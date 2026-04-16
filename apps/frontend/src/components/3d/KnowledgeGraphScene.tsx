"use client";

import type { KnowledgeGraphData } from "@mitonexus/shared-types";
import { OrbitControls, PerspectiveCamera, Stats } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { Bloom, EffectComposer, SSAO } from "@react-three/postprocessing";
import dynamic from "next/dynamic";
import { useMemo, useState } from "react";

import { ForceGraph } from "@/components/3d/ForceGraph";
import { GraphControls } from "@/components/3d/GraphControls";
import { GraphLegend } from "@/components/3d/GraphLegend";

const NodeDetailPanel = dynamic(
  () => import("./NodeDetailPanel").then((module) => module.NodeDetailPanel),
  { ssr: false },
);

type KnowledgeGraphSceneProps = {
  data: KnowledgeGraphData;
};

export default function KnowledgeGraphScene({ data }: KnowledgeGraphSceneProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const selectedNode = useMemo(
    () => data.nodes.find((node) => node.id === selectedNodeId) ?? null,
    [data.nodes, selectedNodeId],
  );

  return (
    <div className="relative h-[calc(100vh-8rem)] w-full overflow-hidden rounded-[2rem] border border-white/10 bg-[radial-gradient(circle_at_top,_rgba(8,145,178,0.18),_transparent_30%),radial-gradient(circle_at_bottom_left,_rgba(249,115,22,0.12),_transparent_30%),linear-gradient(180deg,_#020617_0%,_#0f172a_55%,_#111827_100%)] shadow-[0_36px_120px_-70px_rgba(15,23,42,1)]">
      <Canvas dpr={[1, 2]}>
        <PerspectiveCamera fov={50} makeDefault position={[0, 0, 820]} />
        <color args={["#020617"]} attach="background" />
        <fog args={["#020617", 900, 1800]} attach="fog" />

        <ambientLight intensity={0.55} />
        <pointLight intensity={1.1} position={[220, 180, 260]} />
        <pointLight color="#0ea5e9" intensity={0.7} position={[-280, -160, -220]} />

        <ForceGraph
          edges={data.edges}
          nodes={data.nodes}
          onNodeClick={setSelectedNodeId}
          positions={data.precomputed_positions}
        />

        <OrbitControls autoRotate autoRotateSpeed={0.18} dampingFactor={0.06} enableDamping />

        <EffectComposer>
          <Bloom intensity={0.95} luminanceSmoothing={0.92} luminanceThreshold={0.36} />
          <SSAO intensity={6} radius={0.22} />
        </EffectComposer>

        {process.env.NODE_ENV === "development" ? <Stats /> : null}
      </Canvas>

      <GraphLegend />
      <GraphControls
        edgeCount={data.edges.length}
        layout={data.layout}
        nodeCount={data.nodes.length}
      />

      {selectedNode ? (
        <NodeDetailPanel node={selectedNode} onClose={() => setSelectedNodeId(null)} />
      ) : null}
    </div>
  );
}
