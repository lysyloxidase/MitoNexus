"use client";

import type { ETCComplexState } from "@mitonexus/shared-types";
import { Html } from "@react-three/drei";
import { memo, useEffect, useMemo, useState } from "react";
import * as THREE from "three";

import { ETCComplex } from "@/components/3d/ETCComplex";

type ETCComplexOverlayProps = {
  state: ETCComplexState;
  targetObject?: THREE.Object3D | null;
  fallbackPosition: [number, number, number];
};

function ETCComplexOverlayComponent({
  state,
  targetObject,
  fallbackPosition,
}: ETCComplexOverlayProps) {
  const [hovered, setHovered] = useState(false);
  const color = useMemo(() => activityToColor(state.activity), [state.activity]);

  useEffect(() => {
    if (!targetObject) {
      return;
    }

    const originalMaterials = new Map<THREE.Mesh, THREE.Material | THREE.Material[]>();
    targetObject.traverse((child) => {
      if (!(child instanceof THREE.Mesh)) {
        return;
      }

      originalMaterials.set(child, child.material);
      child.material = new THREE.MeshStandardMaterial({
        color,
        emissive: state.activity < 0.4 ? new THREE.Color("#ef4444") : new THREE.Color(color),
        emissiveIntensity: state.activity < 0.4 ? 0.35 : 0.12,
        metalness: 0.18,
        roughness: 0.42,
      });
    });

    return () => {
      originalMaterials.forEach((material, mesh) => {
        mesh.material = material;
      });
    };
  }, [color, state.activity, targetObject]);

  const position = useMemo<[number, number, number]>(() => {
    if (!targetObject) {
      return fallbackPosition;
    }

    return [targetObject.position.x, targetObject.position.y, targetObject.position.z];
  }, [fallbackPosition, targetObject]);

  return (
    <group position={position}>
      {!targetObject ? (
        <group onPointerOut={() => setHovered(false)} onPointerOver={() => setHovered(true)}>
          <ETCComplex color={color} complexId={state.complex_id} position={[0, 0, 0]} />
        </group>
      ) : null}

      <Html center position={[0, 0.42, 0]} style={{ pointerEvents: "none" }}>
        <div className="rounded-xl border border-white/15 bg-slate-950/85 px-3 py-2 text-xs text-white shadow-xl backdrop-blur">
          <div className="font-semibold">Complex {state.complex_id}</div>
          <div className="text-slate-200">{Math.round(state.activity * 100)}% activity</div>
          {hovered || targetObject ? (
            <div className="mt-1 max-w-52 leading-5 text-slate-300">{state.explanation}</div>
          ) : null}
        </div>
      </Html>
    </group>
  );
}

export const ETCComplexOverlay = memo(ETCComplexOverlayComponent);

function activityToColor(activity: number): THREE.Color {
  const clamped = Math.min(1, Math.max(0, activity));
  const red = clamped < 0.5 ? 1 : 2 * (1 - clamped);
  const green = clamped < 0.5 ? 2 * clamped : 1;
  return new THREE.Color(red, green, 0.28);
}
