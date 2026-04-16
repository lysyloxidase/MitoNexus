import Link from "next/link";

const capabilityCards = [
  {
    title: "41-marker catalog",
    description:
      "CBC, hormones, liver, kidney, lipids, urinalysis, vitamins, electrolytes, thyroid, and homocysteine are wired to a single backend definition set.",
  },
  {
    title: "Mitochondrial mapping",
    description:
      "Every marker carries cascade, gene, pathway, and interpretation metadata so the analysis engine can explain why a value matters.",
  },
  {
    title: "Report workflow",
    description:
      "The form submits to FastAPI, stores the analysis, computes a mito score, and returns a report route for immediate review.",
  },
];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,197,94,0.2),_transparent_35%),radial-gradient(circle_at_left,_rgba(56,189,248,0.18),_transparent_30%),linear-gradient(180deg,_#020617_0%,_#0f172a_55%,_#111827_100%)] text-white">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-6 py-12 sm:px-10 lg:px-12">
        <header className="grid gap-8 border-b border-white/10 pb-12 lg:grid-cols-[1.3fr_0.7fr]">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.32em] text-emerald-300/80">
              Phase 3
            </p>
            <h1 className="mt-4 text-5xl font-semibold tracking-tight text-balance sm:text-6xl">
              Marker analysis is live in the MitoNexus workspace.
            </h1>
            <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-300">
              The platform can now take a structured blood panel, derive key metabolic ratios,
              connect markers to mitochondrial cascades, and persist a first-pass analysis report.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                className="inline-flex items-center justify-center rounded-full bg-emerald-500 px-6 py-3 text-sm font-semibold text-slate-950 shadow-[0_18px_45px_-22px_rgba(16,185,129,0.9)] transition hover:bg-emerald-400"
                href="/analyze"
              >
                Open blood test form
              </Link>
              <Link
                className="inline-flex items-center justify-center rounded-full border border-white/10 bg-white/5 px-6 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
                href="http://localhost:8000/health"
              >
                Backend health
              </Link>
            </div>
          </div>

          <div className="rounded-[2rem] border border-emerald-400/15 bg-emerald-500/10 p-6 shadow-[0_30px_120px_-40px_rgba(2,6,23,0.8)]">
            <p className="text-sm uppercase tracking-[0.22em] text-emerald-200">Current scope</p>
            <dl className="mt-6 space-y-5">
              <div>
                <dt className="text-xs uppercase tracking-[0.18em] text-slate-400">
                  Backend endpoints
                </dt>
                <dd className="mt-2 text-2xl font-semibold">5</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-[0.18em] text-slate-400">
                  Marker definitions
                </dt>
                <dd className="mt-2 text-2xl font-semibold">41</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-[0.18em] text-slate-400">
                  Derived markers
                </dt>
                <dd className="mt-2 text-2xl font-semibold">3</dd>
              </div>
            </dl>
          </div>
        </header>

        <section className="grid gap-6 py-12 md:grid-cols-3">
          {capabilityCards.map((card) => (
            <article
              className="rounded-[1.75rem] border border-white/10 bg-white/[0.04] p-6 shadow-[0_24px_80px_-40px_rgba(15,23,42,0.8)]"
              key={card.title}
            >
              <p className="text-sm uppercase tracking-[0.2em] text-emerald-300">Ready</p>
              <h2 className="mt-4 text-2xl font-semibold">{card.title}</h2>
              <p className="mt-3 text-base leading-7 text-slate-300">{card.description}</p>
            </article>
          ))}
        </section>

        <section className="mt-auto rounded-[2rem] border border-white/10 bg-slate-950/80 px-6 py-8 text-slate-100">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div className="max-w-2xl">
              <p className="text-sm uppercase tracking-[0.22em] text-emerald-300">Next step</p>
              <h2 className="mt-3 text-2xl font-semibold">
                The frontend and backend now speak the same analysis contract.
              </h2>
            </div>
            <p className="text-sm text-slate-300">
              Phase 4 can build on stored reports, therapy workflows, and 3D visualization.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}
