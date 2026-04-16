type GraphControlsProps = {
  nodeCount: number;
  edgeCount: number;
  layout: string;
};

export function GraphControls({ nodeCount, edgeCount, layout }: GraphControlsProps) {
  return (
    <div className="absolute bottom-4 left-4 max-w-sm rounded-[1.5rem] border border-white/10 bg-slate-950/75 p-4 text-white shadow-[0_20px_60px_-40px_rgba(15,23,42,0.9)] backdrop-blur">
      <p className="text-xs uppercase tracking-[0.24em] text-sky-300/75">Scene controls</p>
      <div className="mt-3 grid grid-cols-3 gap-3">
        <StatCard label="Nodes" value={nodeCount} />
        <StatCard label="Edges" value={edgeCount} />
        <StatCard label="Layout" value={layout} />
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-300">
        Drag to orbit, scroll to zoom, and click any node to inspect the patient-specific biomarker,
        cascade, therapy, or pathway context.
      </p>
    </div>
  );
}

type StatCardProps = {
  label: string;
  value: number | string;
};

function StatCard({ label, value }: StatCardProps) {
  return (
    <div className="rounded-[1.1rem] border border-white/8 bg-white/5 p-3">
      <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">{label}</p>
      <p className="mt-2 text-lg font-semibold text-white">{value}</p>
    </div>
  );
}
