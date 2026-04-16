import Link from "next/link";

import { Mitochondrion3D } from "@/components/3d/Mitochondrion3D";

type MitochondrionPageProps = {
  params: Promise<{
    reportId: string;
  }>;
};

export default async function ReportMitochondrionPage({ params }: MitochondrionPageProps) {
  const { reportId } = await params;

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.18),_transparent_24%),radial-gradient(circle_at_bottom_left,_rgba(59,130,246,0.14),_transparent_28%),linear-gradient(180deg,_#020617_0%,_#0f172a_60%,_#111827_100%)] text-white">
      <div className="mx-auto flex min-h-screen max-w-[96rem] flex-col px-4 py-6 sm:px-6 lg:px-8">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-cyan-300/75">
              3D Mitochondrion View
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight">
              ETC overlay and membrane explorer
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-300">
              Inspect the patient-specific mitochondrial overlay for report {reportId}, including
              ETC complex activity gradients and marker-linked annotations.
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
              className="inline-flex items-center justify-center rounded-full border border-cyan-300/25 bg-cyan-400/10 px-5 py-3 text-sm font-semibold text-cyan-50 transition hover:bg-cyan-400/20"
              href={`/report/${reportId}/graph`}
            >
              Open 3D graph
            </Link>
          </div>
        </div>

        <Mitochondrion3D reportId={reportId} />
      </div>
    </main>
  );
}
