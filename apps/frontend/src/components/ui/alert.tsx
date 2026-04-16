import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type AlertProps = HTMLAttributes<HTMLDivElement> & {
  tone?: "error" | "info" | "success";
};

const toneClasses: Record<NonNullable<AlertProps["tone"]>, string> = {
  error: "border-rose-400/40 bg-rose-500/10 text-rose-100",
  info: "border-sky-400/40 bg-sky-500/10 text-sky-100",
  success: "border-emerald-400/40 bg-emerald-500/10 text-emerald-100",
};

export function Alert({ className, tone = "info", ...props }: AlertProps) {
  return (
    <div
      className={cn("rounded-3xl border px-4 py-3 text-sm leading-6", toneClasses[tone], className)}
      {...props}
    />
  );
}
