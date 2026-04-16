import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import React from "react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ReportVisualizationPayload } from "@mitonexus/shared-types";

import { Mitochondrion3D } from "@/components/3d/Mitochondrion3D";

const fetchVisualizationDataMock =
  vi.fn<(reportId: string) => Promise<ReportVisualizationPayload>>();

vi.mock("next/dynamic", () => ({
  default: (_loader: unknown, options?: { loading?: () => ReactNode }) => {
    return function DynamicScene(props: { visualization?: unknown }) {
      if (!props.visualization && options?.loading) {
        const Loading = options.loading;
        return <Loading />;
      }

      return <div data-testid="mitochondrion-scene">scene ready</div>;
    };
  },
}));

vi.mock("@/lib/api", () => ({
  fetchVisualizationData: (reportId: string) => fetchVisualizationDataMock(reportId),
}));

describe("Mitochondrion3D", () => {
  beforeEach(() => {
    fetchVisualizationDataMock.mockReset();
  });

  it("renders the mitochondrion scene once visualization data loads", async () => {
    fetchVisualizationDataMock.mockResolvedValue({
      knowledge_graph: {
        nodes: [],
        edges: [],
        layout: "hybrid",
        precomputed_positions: null,
      },
      mitochondrion: {
        etc_complexes: [
          {
            complex_id: "I",
            activity: 0.62,
            contributing_markers: ["homocysteine"],
            explanation: "Oxidative pressure suggests reduced reserve.",
          },
        ],
        overall_health: 68,
        annotations: [],
      },
    });

    render(withQueryClient(<Mitochondrion3D reportId="report-456" />));

    expect(await screen.findByTestId("mitochondrion-scene")).toBeInTheDocument();
    expect(fetchVisualizationDataMock).toHaveBeenCalledWith("report-456");
  });
});

function withQueryClient(children: ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
