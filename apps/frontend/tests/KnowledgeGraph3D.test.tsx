import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import React from "react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ReportVisualizationPayload } from "@mitonexus/shared-types";

import { KnowledgeGraph3D } from "@/components/3d/KnowledgeGraph3D";

const fetchVisualizationDataMock =
  vi.fn<(reportId: string) => Promise<ReportVisualizationPayload>>();

vi.mock("next/dynamic", () => ({
  default: (_loader: unknown, options?: { loading?: () => ReactNode }) => {
    return function DynamicScene(props: { data?: unknown }) {
      if (!props.data && options?.loading) {
        const Loading = options.loading;
        return <Loading />;
      }

      return <div data-testid="knowledge-graph-scene">scene ready</div>;
    };
  },
}));

vi.mock("@/lib/api", () => ({
  fetchVisualizationData: (reportId: string) => fetchVisualizationDataMock(reportId),
}));

describe("KnowledgeGraph3D", () => {
  beforeEach(() => {
    fetchVisualizationDataMock.mockReset();
  });

  it("renders the graph scene once visualization data loads", async () => {
    fetchVisualizationDataMock.mockResolvedValue({
      knowledge_graph: {
        nodes: [
          {
            id: "marker:homocysteine",
            type: "marker",
            label: "Homocysteine",
            centrality: 0.7,
            color: "#ef4444",
            size: 12,
            abnormal: true,
            metadata: {},
          },
        ],
        edges: [],
        layout: "hybrid",
        precomputed_positions: null,
      },
      mitochondrion: {
        etc_complexes: [],
        overall_health: 72,
        annotations: [],
      },
    });

    render(withQueryClient(<KnowledgeGraph3D reportId="report-123" />));

    expect(await screen.findByTestId("knowledge-graph-scene")).toBeInTheDocument();
    expect(fetchVisualizationDataMock).toHaveBeenCalledWith("report-123");
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
