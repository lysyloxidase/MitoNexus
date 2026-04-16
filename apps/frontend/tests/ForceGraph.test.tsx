import * as THREE from "three";
import { describe, expect, it } from "vitest";

import {
  LARGE_GRAPH_NODE_THRESHOLD,
  buildForceGraphData,
  findGraphNodeId,
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
});
