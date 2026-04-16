"use client";

type GraphControlsProps = {
  nodeCount: number;
  edgeCount: number;
  layout: string;
  selectedNodeLabel?: string | null;
  selectedSubgraphNodeCount?: number;
  selectedSubgraphEdgeCount?: number;
  viewMode?: "patient" | "full";
  onViewModeChange?: (viewMode: "patient" | "full") => void;
  patientCounts?: {
    markers: number;
    genes: number;
    cascades: number;
    therapies: number;
    pathways: number;
  };
};

export function GraphControls({
  nodeCount,
  edgeCount,
  layout,
  selectedNodeLabel = null,
  selectedSubgraphNodeCount = 0,
  selectedSubgraphEdgeCount = 0,
  viewMode = "patient",
  onViewModeChange,
  patientCounts,
}: GraphControlsProps) {
  return (
    <div className="absolute bottom-4 left-4 max-w-sm rounded-[1.5rem] border border-white/10 bg-slate-950/75 p-4 text-white shadow-[0_20px_60px_-40px_rgba(15,23,42,0.9)] backdrop-blur">
      <p className="text-xs uppercase tracking-[0.24em] text-sky-300/75">Scene controls</p>
      <div className="mt-3 inline-flex rounded-full border border-white/10 bg-white/5 p-1">
        <TogglePill
          active={viewMode === "patient"}
          label="Patient focus"
          onClick={() => onViewModeChange?.("patient")}
        />
        <TogglePill
          active={viewMode === "full"}
          label="Full context"
          onClick={() => onViewModeChange?.("full")}
        />
      </div>
      <div className="mt-3 grid grid-cols-3 gap-3">
        <StatCard label="Nodes" value={nodeCount} />
        <StatCard label="Edges" value={edgeCount} />
        <StatCard label="Layout" value={layout} />
      </div>
      {patientCounts ? (
        <div className="mt-4 rounded-[1.1rem] border border-emerald-400/20 bg-emerald-500/10 p-3 text-sm leading-6 text-emerald-50">
          <p className="text-[11px] uppercase tracking-[0.2em] text-emerald-200/80">
            Patient-targeted map
          </p>
          <div className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-emerald-100/85">
            <span>Markers: {patientCounts.markers}</span>
            <span>Genes: {patientCounts.genes}</span>
            <span>Cascades: {patientCounts.cascades}</span>
            <span>Therapies: {patientCounts.therapies}</span>
            <span>Pathways: {patientCounts.pathways}</span>
          </div>
        </div>
      ) : null}
      {selectedNodeLabel ? (
        <div className="mt-4 rounded-[1.1rem] border border-cyan-400/20 bg-cyan-400/8 p-3 text-sm leading-6 text-cyan-50">
          <p className="text-[11px] uppercase tracking-[0.2em] text-cyan-200/80">Focused path</p>
          <p className="mt-2 font-medium">{selectedNodeLabel}</p>
          <p className="mt-1 text-cyan-100/80">
            Showing {selectedSubgraphNodeCount} related nodes and {selectedSubgraphEdgeCount} edges.
          </p>
        </div>
      ) : null}
      <p className="mt-4 text-sm leading-6 text-slate-300">
        Patient focus shows only the nodes the algorithm considered relevant for this report. Click
        any node to isolate its local biomarker-to-therapy path, or click the background to clear
        the focus.
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

type TogglePillProps = {
  active: boolean;
  label: string;
  onClick: () => void;
};

function TogglePill({ active, label, onClick }: TogglePillProps) {
  return (
    <button
      className={`rounded-full px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] transition ${
        active
          ? "bg-emerald-400 text-slate-950 shadow-[0_10px_30px_-18px_rgba(52,211,153,0.95)]"
          : "text-slate-300 hover:bg-white/8 hover:text-white"
      }`}
      onClick={onClick}
      type="button"
    >
      {label}
    </button>
  );
}
