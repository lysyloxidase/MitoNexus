import Link from "next/link";

import { KnowledgeGraph3D } from "@/components/3d/KnowledgeGraph3D";

type GraphPageProps = {
  params: Promise<{
    reportId: string;
  }>;
};

export default async function ReportGraphPage({ params }: GraphPageProps) {
  const { reportId } = await params;

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(14,165,233,0.18),_transparent_24%),radial-gradient(circle_at_bottom_left,_rgba(249,115,22,0.16),_transparent_24%),linear-gradient(180deg,_#020617_0%,_#0f172a_60%,_#111827_100%)] text-white">
      <div className="mx-auto flex min-h-screen max-w-[96rem] flex-col px-4 py-6 sm:px-6 lg:px-8">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-sky-300/75">3D Graph View</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight">Knowledge graph explorer</h1>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-300">
              Rotate through the mitochondrial interaction map to inspect abnormal markers,
              cascades, linked genes, and therapy hypotheses for report {reportId}.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link
              className="inline-flex items-center justify-center rounded-full border border-white/10 bg-white/5 px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
              href={`/report/${reportId}`}
            >
              Back to report
            </Link>
            <Link
              className="inline-flex items-center justify-center rounded-full bg-emerald-500 px-5 py-3 text-sm font-semibold text-slate-950 shadow-[0_18px_45px_-22px_rgba(16,185,129,0.9)] transition hover:bg-emerald-400"
              href="/analyze"
            >
              Run another analysis
            </Link>
          </div>
        </div>

        <KnowledgeGraph3D reportId={reportId} />
      </div>
    </main>
  );
}
