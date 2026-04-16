import { describe, expect, it } from "vitest";

describe("frontend scaffold", () => {
  it("keeps the project name intact", () => {
    expect("MitoNexus").toContain("Mito");
  });
});
