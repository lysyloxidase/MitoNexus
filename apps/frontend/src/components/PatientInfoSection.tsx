"use client";

import type { UseFormReturn } from "react-hook-form";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { BloodTestFormValues } from "@/types/blood-test";

type PatientInfoSectionProps = {
  form: UseFormReturn<BloodTestFormValues>;
};

export function PatientInfoSection({ form }: PatientInfoSectionProps) {
  const selectedSex = form.watch("patientSex");

  return (
    <Card>
      <CardHeader>
        <CardTitle>Patient Context</CardTitle>
        <CardDescription>
          Age, biological sex, and test date define the reference intervals used by the marker
          engine.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-3">
        <div className="space-y-2">
          <Label htmlFor="patientAge">Age</Label>
          <Input
            id="patientAge"
            max={120}
            min={18}
            step={1}
            type="number"
            {...form.register("patientAge", { valueAsNumber: true })}
          />
        </div>
        <div className="space-y-3">
          <Label>Sex</Label>
          <div className="flex gap-3">
            {(["M", "F"] as const).map((sex) => (
              <label
                className="flex flex-1 cursor-pointer items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-200"
                key={sex}
              >
                <input
                  checked={selectedSex === sex}
                  className="h-4 w-4"
                  type="radio"
                  value={sex}
                  {...form.register("patientSex")}
                />
                {sex === "M" ? "Male" : "Female"}
              </label>
            ))}
          </div>
        </div>
        <div className="space-y-2">
          <Label htmlFor="testDate">Test date</Label>
          <Input id="testDate" type="date" {...form.register("testDate")} />
        </div>
      </CardContent>
    </Card>
  );
}
