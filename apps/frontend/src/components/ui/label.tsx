import type { LabelHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Label({ className, ...props }: LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    /* biome-ignore lint/a11y/noLabelWithoutControl: reusable label component forwards htmlFor or wraps a form control. */
    <label
      className={cn("text-sm font-medium tracking-wide text-slate-200", className)}
      {...props}
    />
  );
}
