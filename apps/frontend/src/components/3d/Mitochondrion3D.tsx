"use client";

import { useQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";

import { Alert } from "@/components/ui/alert";
import { fetchVisualizationData } from "@/lib/api";

import { MitoLoadingPlaceholder } from "./MitoLoadingPlaceholder";

const MitochondrionScene = dynamic(() => import("./MitochondrionScene"), {
  ssr: false,
  loading: () => <MitoLoadingPlaceholder />,
});

type Mitochondrion3DProps = {
  reportId: string;
};

export function Mitochondrion3D({ reportId }: Mitochondrion3DProps) {
  const visualizationQuery = useQuery({
    queryKey: ["report-visualization", reportId],
    queryFn: () => fetchVisualizationData(reportId),
  });

  if (visualizationQuery.isPending) {
    return <MitoLoadingPlaceholder />;
  }

  if (visualizationQuery.isError) {
    return (
      <Alert tone="error">
        {visualizationQuery.error instanceof Error
          ? visualizationQuery.error.message
          : "The mitochondrion overlay could not be loaded."}
      </Alert>
    );
  }

  if (!visualizationQuery.data?.mitochondrion) {
    return <Alert tone="error">No mitochondrion overlay is available for this report yet.</Alert>;
  }

  return <MitochondrionScene visualization={visualizationQuery.data.mitochondrion} />;
}
