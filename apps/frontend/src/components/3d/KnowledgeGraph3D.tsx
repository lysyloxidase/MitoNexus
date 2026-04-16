"use client";

import { useQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import { Suspense } from "react";

import { GraphLoadingPlaceholder } from "@/components/3d/GraphLoadingPlaceholder";
import { Alert } from "@/components/ui/alert";
import { fetchVisualizationData } from "@/lib/api";

const KnowledgeGraphScene = dynamic(() => import("./KnowledgeGraphScene"), {
  ssr: false,
  loading: () => <GraphLoadingPlaceholder />,
});

type KnowledgeGraph3DProps = {
  reportId: string;
};

export function KnowledgeGraph3D({ reportId }: KnowledgeGraph3DProps) {
  const visualizationQuery = useQuery({
    queryKey: ["report-visualization", reportId],
    queryFn: () => fetchVisualizationData(reportId),
  });

  if (visualizationQuery.isPending) {
    return <GraphLoadingPlaceholder />;
  }

  if (visualizationQuery.isError) {
    return (
      <Alert tone="error">
        {visualizationQuery.error instanceof Error
          ? visualizationQuery.error.message
          : "The knowledge graph could not be loaded."}
      </Alert>
    );
  }

  const data = visualizationQuery.data;
  if (!data?.knowledge_graph) {
    return <Alert tone="error">This report does not include knowledge graph data yet.</Alert>;
  }

  return (
    <Suspense fallback={<GraphLoadingPlaceholder />}>
      <KnowledgeGraphScene data={data.knowledge_graph} />
    </Suspense>
  );
}
