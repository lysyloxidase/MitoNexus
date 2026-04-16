const foundationAreas = [
  {
    title: "Backend shell",
    description: "FastAPI, settings, tests, linting, and Docker image wiring are in place.",
  },
  {
    title: "Frontend shell",
    description: "Next.js, React 19, Tailwind, Biome, and Vitest are scaffolded for iteration.",
  },
  {
    title: "Data services",
    description: "Postgres, Redis, Neo4j, Ollama, and Langfuse are composed for local development.",
  },
];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(114,183,143,0.18),_transparent_42%),linear-gradient(180deg,_#f6f8f3_0%,_#edf1e8_100%)] text-slate-950">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-6 py-12 sm:px-10 lg:px-12">
        <header className="flex flex-col gap-6 border-b border-slate-900/10 pb-10">
          <p className="text-sm font-medium uppercase tracking-[0.3em] text-emerald-800/80">
            Phase 1 Scaffold
          </p>
          <div className="max-w-3xl space-y-4">
            <h1 className="text-5xl font-semibold tracking-tight text-balance sm:text-6xl">
              MitoNexus is ready for platform work.
            </h1>
            <p className="max-w-2xl text-lg leading-8 text-slate-700">
              This workspace establishes the monorepo, infrastructure, and developer toolchain for
              an AI/ML platform focused on personalized mitochondrial health therapy.
            </p>
          </div>
        </header>

        <section className="grid gap-6 py-12 md:grid-cols-3">
          {foundationAreas.map((item) => (
            <article
              key={item.title}
              className="rounded-3xl border border-slate-900/10 bg-white/70 p-6 shadow-[0_24px_80px_-40px_rgba(15,23,42,0.45)] backdrop-blur"
            >
              <p className="text-sm font-medium uppercase tracking-[0.2em] text-emerald-700">
                Ready
              </p>
              <h2 className="mt-4 text-2xl font-semibold">{item.title}</h2>
              <p className="mt-3 text-base leading-7 text-slate-700">{item.description}</p>
            </article>
          ))}
        </section>

        <section className="mt-auto rounded-[2rem] border border-emerald-900/10 bg-slate-950 px-6 py-8 text-slate-100 shadow-[0_30px_120px_-40px_rgba(2,6,23,0.75)]">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div className="max-w-2xl">
              <p className="text-sm uppercase tracking-[0.2em] text-emerald-300">Next step</p>
              <h2 className="mt-3 text-2xl font-semibold">
                Features start after the platform foundation is green.
              </h2>
            </div>
            <p className="text-sm text-slate-300">
              Health endpoint, CI workflows, strict typing, and Docker services are the current
              contract.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}
