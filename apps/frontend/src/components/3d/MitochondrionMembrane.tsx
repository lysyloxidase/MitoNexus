"use client";

import { memo } from "react";

type MitochondrionMembraneProps = {
  scale: [number, number, number];
  color: string;
  opacity: number;
  wireframe?: boolean;
};

function MitochondrionMembraneComponent({
  scale,
  color,
  opacity,
  wireframe = false,
}: MitochondrionMembraneProps) {
  return (
    <mesh scale={scale}>
      <icosahedronGeometry args={[1, 5]} />
      <meshPhysicalMaterial
        color={color}
        opacity={opacity}
        roughness={0.35}
        transparent
        transmission={0.15}
        wireframe={wireframe}
      />
    </mesh>
  );
}

export const MitochondrionMembrane = memo(MitochondrionMembraneComponent);
