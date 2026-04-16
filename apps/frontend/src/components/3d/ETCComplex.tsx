"use client";

import { memo } from "react";
import type * as THREE from "three";

type ETCComplexProps = {
  complexId: "I" | "II" | "III" | "IV" | "V";
  color: THREE.ColorRepresentation;
  position: [number, number, number];
  scale?: number;
};

function ETCComplexComponent({ complexId, color, position, scale = 1 }: ETCComplexProps) {
  return (
    <mesh position={position} scale={scale}>
      {complexId === "I" ? <boxGeometry args={[0.45, 0.24, 0.18]} /> : null}
      {complexId === "II" ? <octahedronGeometry args={[0.16, 0]} /> : null}
      {complexId === "III" ? <cylinderGeometry args={[0.14, 0.14, 0.38, 24]} /> : null}
      {complexId === "IV" ? <tetrahedronGeometry args={[0.2, 0]} /> : null}
      {complexId === "V" ? <coneGeometry args={[0.18, 0.42, 24]} /> : null}
      <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.16} />
    </mesh>
  );
}

export const ETCComplex = memo(ETCComplexComponent);
