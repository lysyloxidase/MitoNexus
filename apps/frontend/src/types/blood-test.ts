import type {
  AnalysisReportPayload,
  AnalysisResponse,
  BloodTestInputPayload,
  MarkerCategory,
  MarkerDefinition,
} from "@mitonexus/shared-types";

export type { AnalysisReportPayload, AnalysisResponse, BloodTestInputPayload, MarkerDefinition };

export type MarkerFieldState = {
  value: string;
  unit: string;
  notTested: boolean;
};

export type BloodTestFormValues = {
  patientAge: number;
  patientSex: "M" | "F";
  testDate: string;
  markers: Record<string, MarkerFieldState>;
};

export const CATEGORY_LABELS: Record<MarkerCategory, string> = {
  complete_blood_count: "Complete Blood Count",
  hormones: "Hormones",
  prostate: "Prostate",
  metabolic: "Metabolic",
  liver: "Liver",
  kidney: "Kidney",
  lipids: "Lipids",
  urinalysis: "Urinalysis",
  vitamins: "Vitamins",
  electrolytes: "Electrolytes",
  thyroid: "Thyroid",
  inflammation: "Inflammation",
};

export function buildFormDefaults(markers: MarkerDefinition[]): BloodTestFormValues {
  return {
    patientAge: 35,
    patientSex: "F",
    testDate: new Date().toISOString().slice(0, 10),
    markers: Object.fromEntries(
      markers.map((marker) => [
        marker.id,
        {
          value: "",
          unit: marker.unit_si,
          notTested: false,
        },
      ]),
    ),
  };
}

export function groupMarkersByCategory(markers: MarkerDefinition[]) {
  return Object.entries(
    markers.reduce<Record<MarkerCategory, MarkerDefinition[]>>(
      (accumulator, marker) => {
        accumulator[marker.category] = [...(accumulator[marker.category] ?? []), marker];
        return accumulator;
      },
      {} as Record<MarkerCategory, MarkerDefinition[]>,
    ),
  ).map(([categoryId, categoryMarkers]) => ({
    id: categoryId as MarkerCategory,
    label: CATEGORY_LABELS[categoryId as MarkerCategory],
    markers: categoryMarkers.sort((left, right) => left.name.localeCompare(right.name)),
  }));
}
