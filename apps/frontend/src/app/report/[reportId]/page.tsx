"use client";

import type { AnalysisReportPayload } from "@mitonexus/shared-types";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { Alert } from "@/components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchJson } from "@/lib/api";

type ReportPageProps = {
  params: {
    reportId: string;
  };
};

export default function ReportPage({ params }: ReportPageProps) {
  const reportQuery = useQuery({
    queryKey: ["report", params.reportId],
    queryFn: () => fetchJson<AnalysisReportPayload>(`/api/v1/report/${params.reportId}`),
    refetchInterval: (query) => (query.state.data?.status === "processing" ? 3000 : false),
  });

  const report = reportQuery.data;
  const priorityTherapies = getPriorityTherapies(report);

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.18),_transparent_30%),linear-gradient(180deg,_#020617_0%,_#0f172a_55%,_#111827_100%)] text-white">
      <div className="mx-auto max-w-6xl px-6 py-10 sm:px-10">
        <div className="flex flex-col gap-6 pb-8">
          <Link className="text-sm uppercase tracking-[0.22em] text-emerald-300" href="/">
            MitoNexus
          </Link>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.25em] text-emerald-300/80">Report</p>
              <h1 className="mt-3 text-4xl font-semibold tracking-tight">Analysis overview</h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-slate-300">
                This page reflects the stored report payload created by the multi-agent workflow.
              </p>
            </div>
            <Link
              className="inline-flex w-fit items-center justify-center rounded-full bg-emerald-500 px-5 py-3 text-sm font-semibold text-slate-950 shadow-[0_18px_45px_-22px_rgba(16,185,129,0.9)] transition hover:bg-emerald-400"
              href="/analyze"
            >
              Run another analysis
            </Link>
          </div>
        </div>

        {reportQuery.isPending ? <Alert>Loading report...</Alert> : null}
        {reportQuery.isError ? (
          <Alert tone="error">
            {reportQuery.error instanceof Error
              ? reportQuery.error.message
              : "The report could not be loaded."}
          </Alert>
        ) : null}
        {report?.status === "processing" ? (
          <Alert>
            Analysis is still running. This page will refresh automatically as the workflow
            finishes.
          </Alert>
        ) : null}
        {report?.status === "failed" ? (
          <Alert tone="error">
            {report.error_message ?? "The workflow failed before the report could be completed."}
          </Alert>
        ) : null}

        {report ? (
          <div className="grid gap-6">
            <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
              <Card>
                <CardHeader>
                  <CardDescription>Composite score</CardDescription>
                  <CardTitle className="text-5xl">{Math.round(report.mitoscore ?? 0)}</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {Object.entries(report.mitoscore_components ?? {}).map(([label, value]) => (
                    <div
                      className="rounded-[1.25rem] border border-white/10 bg-white/5 p-4"
                      key={label}
                    >
                      <p className="text-xs uppercase tracking-[0.18em] text-slate-400">
                        {label.replaceAll("_", " ")}
                      </p>
                      <p className="mt-2 text-2xl font-semibold text-white">{Math.round(value)}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardDescription>Priority therapies</CardDescription>
                  <CardTitle>Actionable shortlist</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {priorityTherapies.length > 0 ? (
                    priorityTherapies.map((therapy) => (
                      <div
                        className="rounded-[1.2rem] border border-emerald-400/20 bg-emerald-500/10 p-4"
                        key={therapy.therapy_id}
                      >
                        <div className="flex items-center justify-between gap-3">
                          <p className="font-semibold text-white">
                            {therapy.therapy_id.replaceAll("_", " ")}
                          </p>
                          <span className="text-sm text-emerald-100/80">{therapy.score} pts</span>
                        </div>
                        <p className="mt-2 text-sm text-emerald-50/90">
                          Markers: {therapy.supporting_markers.join(", ") || "none"} | Cascades:{" "}
                          {therapy.supporting_cascades.join(", ") || "none"}
                        </p>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-slate-300">
                      No priority therapies were attached to this report yet.
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardDescription>Abnormal markers</CardDescription>
                  <CardTitle>Marker findings</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {report.marker_analyses
                    .filter((analysis) => analysis.status !== "optimal")
                    .slice(0, 10)
                    .map((analysis) => (
                      <div
                        className="rounded-[1.2rem] border border-white/10 bg-white/5 p-4"
                        key={analysis.marker_id}
                      >
                        <div className="flex items-center justify-between gap-3">
                          <p className="font-semibold text-white">{analysis.marker_name}</p>
                          <span className="text-sm uppercase tracking-[0.12em] text-slate-300">
                            {analysis.status.replaceAll("_", " ")}
                          </span>
                        </div>
                        <p className="mt-2 text-sm text-slate-300">
                          {analysis.value} {analysis.unit}
                        </p>
                        <p className="mt-3 text-sm leading-6 text-slate-400">
                          {analysis.mito_interpretation}
                        </p>
                      </div>
                    ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardDescription>Affected cascades</CardDescription>
                  <CardTitle>Signaling overview</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {report.cascade_assessments
                    .filter((assessment) => assessment.status !== "optimal")
                    .slice(0, 10)
                    .map((assessment) => (
                      <div
                        className="rounded-[1.2rem] border border-white/10 bg-white/5 p-4"
                        key={assessment.cascade_id}
                      >
                        <div className="flex items-center justify-between gap-3">
                          <p className="font-semibold text-white">{assessment.name}</p>
                          <span className="text-sm uppercase tracking-[0.12em] text-slate-300">
                            {assessment.status.replaceAll("_", " ")}
                          </span>
                        </div>
                        <p className="mt-3 text-sm leading-6 text-slate-400">
                          {assessment.impact_explanation}
                        </p>
                      </div>
                    ))}
                </CardContent>
              </Card>
            </div>
          </div>
        ) : null}
      </div>
    </main>
  );
}

type PriorityTherapy = {
  therapy_id: string;
  supporting_markers: string[];
  supporting_cascades: string[];
  score: number;
};

function getPriorityTherapies(report: AnalysisReportPayload | undefined): PriorityTherapy[] {
  const rawPlan = report?.therapy_plan;
  if (!rawPlan || typeof rawPlan !== "object") {
    return [];
  }

  const rawTherapies = rawPlan.priority_therapies;
  if (!Array.isArray(rawTherapies)) {
    return [];
  }

  return rawTherapies
    .filter((therapy): therapy is PriorityTherapy => {
      if (!therapy || typeof therapy !== "object") {
        return false;
      }

      const candidate = therapy as Record<string, unknown>;
      return (
        typeof candidate.therapy_id === "string" &&
        Array.isArray(candidate.supporting_markers) &&
        Array.isArray(candidate.supporting_cascades) &&
        typeof candidate.score === "number"
      );
    })
    .slice(0, 6);
}
