import { cn } from "@/lib/utils";

type GraphLoadingPlaceholderProps = {
  className?: string;
};

export function GraphLoadingPlaceholder({ className }: GraphLoadingPlaceholderProps) {
  return (
    <div
      className={cn(
        "flex min-h-[32rem] w-full items-center justify-center rounded-[2rem] border border-white/10 bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.14),_transparent_35%),linear-gradient(180deg,_rgba(2,6,23,0.98),_rgba(15,23,42,0.96))] p-6 text-white shadow-[0_28px_90px_-60px_rgba(14,165,233,0.5)]",
        className,
      )}
    >
      <div className="w-full max-w-3xl space-y-5">
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.3em] text-emerald-300/80">
            Rendering Knowledge Graph
          </p>
          <h2 className="text-3xl font-semibold tracking-tight">
            Loading the mitochondrial network scene
          </h2>
          <p className="max-w-2xl text-sm leading-6 text-slate-300">
            Pulling the patient-specific graph, precomputed layout, and overlay controls into the 3D
            scene.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          {["signals", "clusters", "therapies"].map((cardKey) => (
            <div className="rounded-[1.5rem] border border-white/10 bg-white/5 p-4" key={cardKey}>
              <div className="h-2 w-24 animate-pulse rounded-full bg-white/15" />
              <div className="mt-4 h-20 animate-pulse rounded-[1.25rem] bg-white/8" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
