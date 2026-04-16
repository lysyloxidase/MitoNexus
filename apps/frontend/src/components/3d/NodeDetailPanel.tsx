"use client";

import type { GraphNode } from "@mitonexus/shared-types";
import { X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { NODE_COLOR_MAP, NODE_LABEL_MAP } from "@/lib/graph-styling";

type NodeDetailPanelProps = {
  node: GraphNode;
  onClose: () => void;
};

export function NodeDetailPanel({ node, onClose }: NodeDetailPanelProps) {
  const metadataEntries = Object.entries(node.metadata).filter(([, value]) => value !== null);

  return (
    <aside className="absolute right-4 top-4 z-10 w-[24rem] max-w-[calc(100vw-2rem)] rounded-[1.75rem] border border-white/10 bg-slate-950/90 p-6 text-white shadow-[0_28px_80px_-42px_rgba(15,23,42,0.95)] backdrop-blur">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-400">
            {NODE_LABEL_MAP[node.type]}
          </p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight">{node.label}</h2>
        </div>
        <Button
          aria-label="Close node details"
          className="h-10 w-10 rounded-full px-0"
          onClick={onClose}
          variant="ghost"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div className="mt-4 flex items-center gap-3">
        <span
          className="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-white"
          style={{
            backgroundColor: `${NODE_COLOR_MAP[node.type]}33`,
            border: `1px solid ${NODE_COLOR_MAP[node.type]}66`,
          }}
        >
          {NODE_LABEL_MAP[node.type]}
        </span>
        <span className="text-sm text-slate-300">Centrality {node.centrality.toFixed(2)}</span>
      </div>

      {node.abnormal ? (
        <p className="mt-4 rounded-2xl border border-rose-400/25 bg-rose-500/10 px-4 py-3 text-sm leading-6 text-rose-100">
          This node is flagged as abnormal in the current patient context.
        </p>
      ) : null}

      <div className="mt-5 space-y-4">
        {metadataEntries.length > 0 ? (
          metadataEntries.map(([key, value]) => (
            <div className="rounded-[1.2rem] border border-white/8 bg-white/5 p-4" key={key}>
              <p className="text-[11px] uppercase tracking-[0.2em] text-slate-400">
                {key.replaceAll("_", " ")}
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-100">{formatValue(value)}</p>
            </div>
          ))
        ) : (
          <div className="rounded-[1.2rem] border border-white/8 bg-white/5 p-4 text-sm leading-6 text-slate-300">
            No additional metadata is attached to this node yet.
          </div>
        )}
      </div>
    </aside>
  );
}

function formatValue(value: unknown): string {
  if (Array.isArray(value)) {
    return value.map((item) => formatValue(item)).join(", ");
  }
  if (typeof value === "object" && value !== null) {
    return JSON.stringify(value, null, 2);
  }
  return String(value);
}
