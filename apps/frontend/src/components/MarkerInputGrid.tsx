"use client";

import type { MarkerDefinition } from "@mitonexus/shared-types";
import type { UseFormReturn } from "react-hook-form";

import { MarkerInput } from "@/components/MarkerInput";
import type { BloodTestFormValues } from "@/types/blood-test";

type MarkerInputGridProps = {
  form: UseFormReturn<BloodTestFormValues>;
  markers: MarkerDefinition[];
  patientSex: "M" | "F";
};

export function MarkerInputGrid({ form, markers, patientSex }: MarkerInputGridProps) {
  return (
    <div className="grid gap-4 xl:grid-cols-2">
      {markers.map((marker) => (
        <MarkerInput form={form} key={marker.id} marker={marker} patientSex={patientSex} />
      ))}
    </div>
  );
}
