import { AppChip } from "@/components/ui/app-chip";

type HeroBannerProps = {
  apiStatus: string;
  apiSubtitle: string;
  activeQueueCount: number;
  staleRunsCount: number;
  backlogCount: number;
};

export function HeroBanner({
  apiStatus,
  apiSubtitle,
  activeQueueCount,
  staleRunsCount,
  backlogCount,
}: HeroBannerProps) {
  return (
    <section className="relative overflow-hidden rounded-4xl border border-white/10 bg-white/5 p-8 shadow-[0_20px_70px_rgba(0,0,0,0.28)] backdrop-blur md:p-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(34,211,238,0.16),transparent_20%),radial-gradient(circle_at_left,rgba(59,130,246,0.12),transparent_30%)]" />
      <div className="relative">
        <div className="flex flex-wrap gap-2">
          <AppChip label="V2" />
          <AppChip label="Step 25" />
          <AppChip label="Full Product Console" />
        </div>

        <div className="mt-6 max-w-4xl">
          <h2 className="text-4xl font-semibold leading-tight tracking-tight text-white md:text-5xl">
            Turn operational pain signals into visible, actionable product
            decisions.
          </h2>
          <p className="mt-5 max-w-3xl text-base leading-7 text-white/68 md:text-lg">
            This console now exposes live platform health, pipeline observability,
            run diagnostics, event timelines, and human-review workflows on top
            of the backend capabilities built through Steps 1–24.
          </p>
        </div>

        <div className="mt-8 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-3xl border border-white/10 bg-black/10 p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/45">
              Product readiness
            </p>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-white/45">
                  Active queue
                </p>
                <p className="mt-2 text-2xl font-semibold text-white">
                  {activeQueueCount}
                </p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-white/45">
                  Stale runs
                </p>
                <p className="mt-2 text-2xl font-semibold text-amber-300">
                  {staleRunsCount}
                </p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-white/45">
                  Review backlog
                </p>
                <p className="mt-2 text-2xl font-semibold text-cyan-200">
                  {backlogCount}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-cyan-400/20 bg-cyan-400/8 p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-100/70">
              Current system status
            </p>
            <p className="mt-3 text-2xl font-semibold text-white">{apiStatus}</p>
            <p className="mt-2 text-sm leading-6 text-white/65">{apiSubtitle}</p>
          </div>
        </div>
      </div>
    </section>
  );
}