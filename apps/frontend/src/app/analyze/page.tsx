"use client";

import type {
  AnalysisResponse,
  BloodTestInputPayload,
  MarkerDefinition,
} from "@mitonexus/shared-types";
import { useMutation, useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useForm } from "react-hook-form";

import { MarkerInputGrid } from "@/components/MarkerInputGrid";
import { PatientInfoSection } from "@/components/PatientInfoSection";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchJson } from "@/lib/api";
import {
  type BloodTestFormValues,
  buildFormDefaults,
  groupMarkersByCategory,
} from "@/types/blood-test";

export default function AnalyzePage() {
  const router = useRouter();
  const form = useForm<BloodTestFormValues>({
    defaultValues: {
      patientAge: 35,
      patientSex: "F",
      testDate: new Date().toISOString().slice(0, 10),
      markers: {},
    },
  });

  const markersQuery = useQuery({
    queryKey: ["markers"],
    queryFn: () => fetchJson<MarkerDefinition[]>("/api/v1/blood-test/markers"),
  });

  useEffect(() => {
    if (!markersQuery.data) {
      return;
    }

    const currentMarkers = form.getValues("markers");
    if (Object.keys(currentMarkers).length > 0) {
      return;
    }

    form.reset(buildFormDefaults(markersQuery.data));
  }, [form, markersQuery.data]);

  const submitMutation = useMutation({
    mutationFn: (payload: BloodTestInputPayload) =>
      fetchJson<AnalysisResponse>("/api/v1/blood-test/analyze", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: (data) => {
      router.push(`/report/${data.report_id}`);
    },
  });

  const groupedMarkers = groupMarkersByCategory(markersQuery.data ?? []);
  const patientSex = form.watch("patientSex");
  const markerEntries = Object.values(form.watch("markers") ?? {}) as Array<
    BloodTestFormValues["markers"][string]
  >;
  const enteredMarkerCount = markerEntries.filter(
    (entry) => !entry.notTested && entry.value.trim() !== "",
  ).length;

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,197,94,0.22),_transparent_34%),radial-gradient(circle_at_right,_rgba(14,165,233,0.16),_transparent_28%),linear-gradient(180deg,_#020617_0%,_#0f172a_55%,_#111827_100%)] text-white">
      <div className="mx-auto max-w-7xl px-6 py-10 sm:px-10 lg:px-12">
        <div className="flex flex-col gap-6 pb-8">
          <Link className="text-sm uppercase tracking-[0.22em] text-emerald-300" href="/">
            MitoNexus
          </Link>
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-sm uppercase tracking-[0.28em] text-emerald-300/80">
                Phase 3 Analysis
              </p>
              <h1 className="mt-3 text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
                Blood test intake with mitochondrial context.
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-slate-300 sm:text-lg">
                Enter the panel once. The marker engine handles range interpretation, derived
                markers, cascade mapping, and report creation from the same backend definitions.
              </p>
            </div>
            <Card className="max-w-sm border-emerald-400/20 bg-emerald-500/10">
              <CardHeader>
                <CardDescription className="text-emerald-100/80">Session snapshot</CardDescription>
                <CardTitle className="text-3xl text-white">{enteredMarkerCount}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-1 text-sm text-emerald-50/90">
                <p>markers entered</p>
                <p>{markersQuery.data?.length ?? 0} supported markers in the current catalog</p>
              </CardContent>
            </Card>
          </div>
        </div>

        {markersQuery.isPending ? <Alert>Loading marker catalog...</Alert> : null}
        {markersQuery.isError ? (
          <Alert tone="error">
            The marker catalog could not be loaded. Make sure the backend API is running and the
            `/api/v1/blood-test/markers` route is reachable.
          </Alert>
        ) : null}
        {submitMutation.isError ? (
          <Alert className="mt-4" tone="error">
            {submitMutation.error instanceof Error
              ? submitMutation.error.message
              : "Blood-test submission failed."}
          </Alert>
        ) : null}

        <div className="mt-8 grid gap-6">
          <PatientInfoSection form={form} />

          <Card>
            <CardHeader>
              <CardTitle>Marker Entry</CardTitle>
              <CardDescription>
                Collapse or expand each category. Every marker uses the same backend catalog for
                ranges, units, and mitochondrial annotations.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Accordion defaultValue={["complete_blood_count"]} type="multiple">
                {groupedMarkers.map((category) => (
                  <AccordionItem key={category.id} value={category.id}>
                    <AccordionTrigger>
                      {category.label}
                      <span className="ml-2 text-sm font-normal text-slate-400">
                        {category.markers.length} markers
                      </span>
                    </AccordionTrigger>
                    <AccordionContent>
                      <MarkerInputGrid
                        form={form}
                        markers={category.markers}
                        patientSex={patientSex}
                      />
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </CardContent>
          </Card>

          <div className="flex flex-col gap-4 rounded-[1.75rem] border border-white/10 bg-white/5 p-5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.22em] text-emerald-300/80">Submission</p>
              <p className="mt-2 text-sm leading-6 text-slate-300">
                Empty or explicitly unchecked markers are excluded from the request payload.
              </p>
            </div>
            <Button
              className="min-w-52"
              disabled={submitMutation.isPending || markersQuery.isPending || markersQuery.isError}
              onClick={form.handleSubmit((values: BloodTestFormValues) => {
                submitMutation.mutate(transformFormValues(values));
              })}
            >
              {submitMutation.isPending ? "Analyzing..." : "Analyze Blood Test"}
            </Button>
          </div>
        </div>
      </div>
    </main>
  );
}

function transformFormValues(values: BloodTestFormValues): BloodTestInputPayload {
  return {
    patient_age: values.patientAge,
    patient_sex: values.patientSex,
    test_date: values.testDate,
    markers: Object.entries(values.markers)
      .filter(([, marker]) => !marker.notTested && marker.value.trim() !== "")
      .map(([markerId, marker]) => ({
        marker_id: markerId,
        value: Number(marker.value),
        unit: marker.unit,
      })),
  };
}
