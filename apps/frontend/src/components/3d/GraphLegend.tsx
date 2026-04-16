import { NODE_COLOR_MAP, NODE_LABEL_MAP } from "@/lib/graph-styling";

export function GraphLegend() {
  return (
    <div className="absolute left-4 top-4 max-w-xs rounded-[1.5rem] border border-white/10 bg-slate-950/75 p-4 text-white shadow-[0_20px_60px_-40px_rgba(15,23,42,0.9)] backdrop-blur">
      <p className="text-xs uppercase tracking-[0.24em] text-emerald-300/75">Node legend</p>
      <div className="mt-4 grid gap-2">
        {Object.entries(NODE_LABEL_MAP).map(([type, label]) => (
          <div className="flex items-center gap-3" key={type}>
            <span
              className="h-3 w-3 rounded-full shadow-[0_0_20px_rgba(255,255,255,0.15)]"
              style={{ backgroundColor: NODE_COLOR_MAP[type as keyof typeof NODE_COLOR_MAP] }}
            />
            <span className="text-sm text-slate-200">{label}</span>
          </div>
        ))}
      </div>
      <div className="mt-4 space-y-2 border-t border-white/10 pt-4 text-sm text-slate-300">
        <p>
          Brighter nodes are directly targeted for this patient by the analysis workflow or therapy
          plan.
        </p>
        <p>Dim nodes are background context from the broader network.</p>
      </div>
    </div>
  );
}
