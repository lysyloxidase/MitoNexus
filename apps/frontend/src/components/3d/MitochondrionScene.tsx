"use client";

import type { ETCComplexState, MitochondrionVisualization } from "@mitonexus/shared-types";
import {
  Environment,
  Html,
  OrbitControls,
  PerspectiveCamera,
  Stars,
  useGLTF,
} from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { Bloom, EffectComposer } from "@react-three/postprocessing";
import { useEffect, useMemo, useState } from "react";

import { ETCComplexOverlay } from "@/components/3d/ETCComplexOverlay";
import { MitoLoadingPlaceholder } from "@/components/3d/MitoLoadingPlaceholder";
import { MitochondrionMembrane } from "@/components/3d/MitochondrionMembrane";

type MitochondrionSceneProps = {
  visualization: MitochondrionVisualization;
};

const COMPLEX_POSITIONS: Record<ETCComplexState["complex_id"], [number, number, number]> = {
  I: [-1.35, 0.2, 0.7],
  II: [-0.72, -0.56, -0.45],
  III: [0, 0.48, 0.95],
  IV: [0.86, -0.08, -0.78],
  V: [1.42, 0.34, 0.32],
};

export default function MitochondrionScene({ visualization }: MitochondrionSceneProps) {
  const [hasGlbModel, setHasGlbModel] = useState(false);

  useEffect(() => {
    let active = true;

    void fetch("/models/mitochondrion.glb", { method: "HEAD" })
      .then((response) => {
        if (active) {
          setHasGlbModel(response.ok);
        }
      })
      .catch(() => {
        if (active) {
          setHasGlbModel(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="relative h-[calc(100vh-8rem)] w-full overflow-hidden rounded-[2rem] border border-white/10 bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.18),_transparent_28%),radial-gradient(circle_at_bottom_left,_rgba(56,189,248,0.12),_transparent_24%),linear-gradient(180deg,_#020617_0%,_#0f172a_55%,_#111827_100%)] shadow-[0_36px_120px_-70px_rgba(15,23,42,1)]">
      <Canvas dpr={[1, 2]} shadows>
        <PerspectiveCamera fov={44} makeDefault position={[0, 0, 6.2]} />
        <color args={["#020617"]} attach="background" />

        <ambientLight intensity={0.45} />
        <directionalLight castShadow intensity={0.9} position={[5, 5, 4]} />
        <pointLight color="#22d3ee" intensity={0.55} position={[-4, -2, -2]} />
        <Environment preset="studio" />
        <Stars count={1200} factor={4} fade radius={22} speed={0.45} />

        {hasGlbModel ? (
          <GlbMitochondrion etcStates={visualization.etc_complexes} />
        ) : (
          <ProceduralMitochondrion
            annotations={visualization.annotations}
            etcStates={visualization.etc_complexes}
            overallHealth={visualization.overall_health}
          />
        )}

        <OrbitControls autoRotate autoRotateSpeed={0.2} dampingFactor={0.06} enableDamping />

        <EffectComposer>
          <Bloom intensity={0.72} luminanceThreshold={0.48} luminanceSmoothing={0.95} />
        </EffectComposer>
      </Canvas>

      <div className="pointer-events-none absolute left-4 top-4 max-w-xs rounded-[1.5rem] border border-white/10 bg-slate-950/72 p-4 text-white backdrop-blur">
        <p className="text-xs uppercase tracking-[0.24em] text-cyan-300/80">Patient Overlay</p>
        <h2 className="mt-3 text-2xl font-semibold tracking-tight">Mitochondrion status</h2>
        <p className="mt-2 text-sm leading-6 text-slate-300">
          ETC activity shading reflects the report-specific mitochondrial pressure pattern.
        </p>
        <div className="mt-4 flex items-end gap-3">
          <span className="text-4xl font-semibold">{Math.round(visualization.overall_health)}</span>
          <span className="pb-1 text-sm uppercase tracking-[0.2em] text-slate-400">overall</span>
        </div>
      </div>
    </div>
  );
}

function GlbMitochondrion({ etcStates }: { etcStates: ETCComplexState[] }) {
  const gltf = useGLTF("/models/mitochondrion.glb");

  return (
    <group>
      <primitive object={gltf.scene} />
      {etcStates.map((state) => (
        <ETCComplexOverlay
          fallbackPosition={COMPLEX_POSITIONS[state.complex_id]}
          key={state.complex_id}
          state={state}
          targetObject={gltf.scene.getObjectByName(`Complex_${state.complex_id}`)}
        />
      ))}
    </group>
  );
}

function ProceduralMitochondrion({
  etcStates,
  overallHealth,
  annotations,
}: {
  etcStates: ETCComplexState[];
  overallHealth: number;
  annotations: Record<string, unknown>[];
}) {
  const annotationPreview = useMemo(() => annotations.slice(0, 3), [annotations]);

  return (
    <group>
      <MitochondrionMembrane color="#67e8f9" opacity={0.11} scale={[2.55, 1.45, 1.2]} />
      <MitochondrionMembrane color="#0ea5e9" opacity={0.08} scale={[2.08, 1.05, 0.88]} wireframe />

      <mesh position={[0, 0, 0]}>
        <torusKnotGeometry args={[0.9, 0.18, 180, 26, 2, 3]} />
        <meshStandardMaterial
          color="#0f766e"
          emissive="#0f766e"
          emissiveIntensity={0.12}
          roughness={0.58}
        />
      </mesh>

      {etcStates.map((state) => (
        <ETCComplexOverlay
          fallbackPosition={COMPLEX_POSITIONS[state.complex_id]}
          key={state.complex_id}
          state={state}
        />
      ))}

      <Html center position={[0, -1.7, 0]}>
        <div className="pointer-events-none rounded-[1.25rem] border border-white/10 bg-slate-950/80 px-4 py-3 text-xs text-white shadow-xl backdrop-blur">
          <div className="font-semibold text-cyan-200">
            Procedural development model {Math.round(overallHealth)} / 100
          </div>
          <div className="mt-1 max-w-72 leading-5 text-slate-300">
            Drop a production `mitochondrion.glb` into `public/models` to replace this placeholder.
          </div>
          {annotationPreview.length > 0 ? (
            <div className="mt-2 border-t border-white/10 pt-2 text-slate-300">
              {annotationPreview.map((annotation, index) => (
                <div key={`${annotation.label ?? "annotation"}-${index}`}>
                  {String(annotation.label ?? "Marker")}: {String(annotation.status ?? "n/a")}
                </div>
              ))}
            </div>
          ) : null}
        </div>
      </Html>
    </group>
  );
}

export { MitoLoadingPlaceholder };
