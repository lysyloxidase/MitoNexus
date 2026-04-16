"use client";

import type { MarkerDefinition, MarkerStatus } from "@mitonexus/shared-types";
import type { UseFormReturn } from "react-hook-form";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import type { BloodTestFormValues } from "@/types/blood-test";

type MarkerInputProps = {
  form: UseFormReturn<BloodTestFormValues>;
  marker: MarkerDefinition;
  patientSex: "M" | "F";
};

type IndicatorState = {
  colorClass: string;
  label: string;
};

const indicatorStyles: Record<MarkerStatus, IndicatorState> = {
  critically_low: { colorClass: "bg-rose-500", label: "Critically low" },
  low: { colorClass: "bg-rose-400", label: "Low" },
  suboptimal_low: { colorClass: "bg-amber-400", label: "Suboptimal low" },
  optimal: { colorClass: "bg-emerald-400", label: "Optimal" },
  suboptimal_high: { colorClass: "bg-amber-400", label: "Suboptimal high" },
  high: { colorClass: "bg-rose-400", label: "High" },
  critically_high: { colorClass: "bg-rose-500", label: "Critically high" },
};

export function MarkerInput({ form, marker, patientSex }: MarkerInputProps) {
  const valueField = `markers.${marker.id}.value` as const;
  const unitField = `markers.${marker.id}.unit` as const;
  const notTestedField = `markers.${marker.id}.notTested` as const;

  const value = form.watch(valueField) ?? "";
  const unit = form.watch(unitField) ?? marker.unit_si;
  const notTested = form.watch(notTestedField) ?? false;
  const indicator = getIndicator(marker, patientSex, value, unit);
  const step =
    typeof marker.metadata?.step === "number" && Number.isFinite(marker.metadata.step)
      ? marker.metadata.step
      : 0.1;

  return (
    <div className="rounded-[1.35rem] border border-white/8 bg-white/[0.03] p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Label htmlFor={valueField}>{marker.name}</Label>
            <span
              className="inline-flex h-5 w-5 items-center justify-center rounded-full border border-white/10 text-[11px] text-slate-300"
              title={getTooltipText(marker, patientSex)}
            >
              i
            </span>
          </div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">
            {marker.unit_si} primary
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-white/10 px-3 py-1 text-xs text-slate-300">
          <span className={cn("h-2.5 w-2.5 rounded-full", indicator.colorClass)} />
          <span>{indicator.label}</span>
        </div>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-[minmax(0,1fr)_11rem]">
        <Input
          id={valueField}
          disabled={notTested}
          min={0}
          placeholder="Enter result"
          step={step}
          type="number"
          {...form.register(valueField)}
        />
        <Select disabled={notTested} {...form.register(unitField)}>
          <option value={marker.unit_si}>{marker.unit_si}</option>
          <option value={marker.unit_conventional}>{marker.unit_conventional}</option>
        </Select>
      </div>

      <label className="mt-3 flex items-center gap-2 text-sm text-slate-300">
        <input
          className="h-4 w-4 rounded border-white/10 bg-white/5"
          type="checkbox"
          {...form.register(notTestedField)}
        />
        Not tested
      </label>
    </div>
  );
}

function getTooltipText(marker: MarkerDefinition, patientSex: "M" | "F"): string {
  const reference = getBounds(marker.reference_range, patientSex);
  const optimal = getBounds(marker.optimal_range, patientSex);
  return `Reference ${formatBounds(reference.min, reference.max)} | Optimal ${formatBounds(optimal.min, optimal.max)} | ${marker.mito_mechanism}`;
}

function getBounds(
  range: MarkerDefinition["reference_range"] | MarkerDefinition["optimal_range"],
  patientSex: "M" | "F",
) {
  if (range.sex_specific) {
    return patientSex === "M"
      ? (range.male ?? { min: range.min, max: range.max })
      : (range.female ?? { min: range.min, max: range.max });
  }
  return { min: range.min, max: range.max };
}

function formatBounds(min: number | null | undefined, max: number | null | undefined): string {
  return `${min ?? "?"}-${max ?? "?"}`;
}

function getIndicator(
  marker: MarkerDefinition,
  patientSex: "M" | "F",
  rawValue: string,
  selectedUnit: string,
): IndicatorState {
  if (rawValue.trim() === "") {
    return { colorClass: "bg-slate-500", label: "No value" };
  }

  const value = Number(rawValue);
  if (!Number.isFinite(value)) {
    return { colorClass: "bg-slate-500", label: "No value" };
  }

  const normalizedValue =
    selectedUnit === marker.unit_conventional ? value * marker.conversion_factor : value;
  const reference = getBounds(marker.reference_range, patientSex);
  const optimal = getBounds(marker.optimal_range, patientSex);
  const status = classifyStatus(
    normalizedValue,
    reference.min ?? null,
    reference.max ?? null,
    optimal.min ?? null,
    optimal.max ?? null,
  );

  return indicatorStyles[status];
}

function classifyStatus(
  value: number,
  refMin: number | null,
  refMax: number | null,
  optMin: number | null,
  optMax: number | null,
): MarkerStatus {
  const span = getReferenceSpan(refMin, refMax);
  const criticalMargin = span * 0.35;

  if (refMin !== null && value < refMin) {
    return value < refMin - criticalMargin ? "critically_low" : "low";
  }
  if (refMax !== null && value > refMax) {
    return value > refMax + criticalMargin ? "critically_high" : "high";
  }
  if (optMin !== null && value < optMin) {
    return "suboptimal_low";
  }
  if (optMax !== null && value > optMax) {
    return "suboptimal_high";
  }
  return "optimal";
}

function getReferenceSpan(refMin: number | null, refMax: number | null): number {
  if (refMin !== null && refMax !== null) {
    return Math.max(refMax - refMin, Math.max(Math.abs(refMax), Math.abs(refMin), 1) * 0.2);
  }
  if (refMin !== null) {
    return Math.max(Math.abs(refMin), 1) * 0.3;
  }
  if (refMax !== null) {
    return Math.max(Math.abs(refMax), 1) * 0.3;
  }
  return 1;
}
