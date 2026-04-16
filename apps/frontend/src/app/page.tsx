import Link from "next/link";

const capabilityCards = [
  {
    title: "Multi-agent mitochondrial reasoning",
    description:
      "LangGraph specialists combine marker interpretation, literature retrieval, therapy prioritization, and final synthesis into one durable workflow.",
  },
  {
    title: "3D visual analytics",
    description:
      "Reports expose both a patient-specific knowledge graph and a mitochondrion overlay so users can inspect systems-level links instead of flat tables.",
  },
  {
    title: "Clinician-ready outputs",
    description:
      "Every completed analysis stores a structured report payload, traceable evidence, and a downloadable PDF summary.",
  },
];

const workflowSteps = [
  "Enter a blood panel and submit the analysis request.",
  "Monitor the asynchronous report while the workflow runs.",
  "Review the MitoScore, cascades, and therapy shortlist.",
  "Inspect the 3D graph and mitochondrion views.",
  "Download the generated PDF report.",
];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.2),_transparent_26%),radial-gradient(circle_at_right,_rgba(56,189,248,0.18),_transparent_24%),linear-gradient(180deg,_#020617_0%,_#0f172a_48%,_#111827_100%)] text-white">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-6 py-12 sm:px-10 lg:px-12">
        <header className="grid gap-10 border-b border-white/10 pb-14 lg:grid-cols-[1.15fr_0.85fr]">
          <div className="max-w-4xl">
            <p className="text-sm font-medium uppercase tracking-[0.32em] text-emerald-300/80">
              MitoNexus v1.0.0
            </p>
            <h1 className="mt-5 text-5xl font-semibold tracking-tight text-balance sm:text-6xl">
              Personalized mitochondrial analysis with 3D clinical context.
            </h1>
            <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-300">
              MitoNexus combines structured biomarker analysis, agentic biomedical reasoning,
              literature-grounded therapy ranking, and rich visual reporting in a single full-stack
              workspace.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                className="inline-flex items-center justify-center rounded-full bg-emerald-500 px-6 py-3 text-sm font-semibold text-slate-950 shadow-[0_18px_45px_-22px_rgba(16,185,129,0.9)] transition hover:bg-emerald-400"
                href="/analyze"
              >
                Launch analysis
              </Link>
              <Link
                className="inline-flex items-center justify-center rounded-full border border-cyan-300/20 bg-cyan-400/10 px-6 py-3 text-sm font-semibold text-cyan-50 transition hover:bg-cyan-400/20"
                href="http://localhost:8000/health"
              >
                Backend health
              </Link>
            </div>
          </div>

          <div className="grid gap-4 rounded-[2rem] border border-white/10 bg-[radial-gradient(circle_at_top_right,_rgba(34,211,238,0.16),_transparent_28%),linear-gradient(180deg,_rgba(15,23,42,0.92),_rgba(2,6,23,0.88))] p-6 shadow-[0_30px_120px_-40px_rgba(2,6,23,0.8)]">
            <div className="rounded-[1.5rem] border border-white/10 bg-white/5 p-5">
              <p className="text-xs uppercase tracking-[0.2em] text-cyan-200">Visual stack</p>
              <p className="mt-3 text-3xl font-semibold">R3F + force graph + ETC overlay</p>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <MetricCard label="Markers" value="41" />
              <MetricCard label="Agents" value="5" />
              <MetricCard label="Views" value="3D + PDF" />
            </div>
            <div className="rounded-[1.5rem] border border-emerald-400/15 bg-emerald-500/10 p-5">
              <p className="text-xs uppercase tracking-[0.2em] text-emerald-200">Outcome</p>
              <p className="mt-3 text-base leading-7 text-emerald-50/90">
                Reports arrive with a MitoScore, evidence-backed therapy plan, a graph explorer, a
                mitochondrion overlay, and PDF export.
              </p>
            </div>
          </div>
        </header>

        <section className="grid gap-6 py-14 md:grid-cols-3">
          {capabilityCards.map((card) => (
            <article
              className="rounded-[1.75rem] border border-white/10 bg-white/[0.04] p-6 shadow-[0_24px_80px_-40px_rgba(15,23,42,0.8)]"
              key={card.title}
            >
              <p className="text-sm uppercase tracking-[0.2em] text-emerald-300">Live</p>
              <h2 className="mt-4 text-2xl font-semibold">{card.title}</h2>
              <p className="mt-3 text-base leading-7 text-slate-300">{card.description}</p>
            </article>
          ))}
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
          <div className="rounded-[2rem] border border-white/10 bg-slate-950/80 p-8">
            <p className="text-sm uppercase tracking-[0.22em] text-cyan-300">Workflow</p>
            <h2 className="mt-4 text-3xl font-semibold tracking-tight">
              From biomarker intake to finished report
            </h2>
            <div className="mt-6 grid gap-4">
              {workflowSteps.map((step, index) => (
                <div
                  className="flex gap-4 rounded-[1.4rem] border border-white/10 bg-white/5 p-4"
                  key={step}
                >
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-cyan-400/15 text-sm font-semibold text-cyan-100">
                    {index + 1}
                  </div>
                  <p className="text-base leading-7 text-slate-200">{step}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[2rem] border border-white/10 bg-[radial-gradient(circle_at_bottom_left,_rgba(16,185,129,0.16),_transparent_32%),linear-gradient(180deg,_rgba(15,23,42,0.92),_rgba(2,6,23,0.88))] p-8">
            <p className="text-sm uppercase tracking-[0.22em] text-emerald-300">Quick start</p>
            <pre className="mt-5 overflow-x-auto rounded-[1.5rem] border border-white/10 bg-slate-950/70 p-5 text-sm leading-7 text-slate-200">
              <code>{`docker compose up -d --build
uv run --directory apps/backend uvicorn mitonexus.main:app --reload
pnpm --filter @mitonexus/frontend dev
uv run --directory apps/backend python scripts/demo.py
open http://localhost:3000/analyze`}</code>
            </pre>
            <p className="mt-5 text-sm leading-7 text-slate-300">
              The demo path seeds a realistic panel, runs the workflow, prints the generated report
              id, and leaves the 3D routes ready to inspect.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1.4rem] border border-white/10 bg-white/5 p-4">
      <p className="text-xs uppercase tracking-[0.18em] text-slate-400">{label}</p>
      <p className="mt-3 text-2xl font-semibold text-white">{value}</p>
    </div>
  );
}
