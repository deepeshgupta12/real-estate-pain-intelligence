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
    <section className="workspace-surface-strong overflow-hidden rounded-4xl p-6 md:p-7">
      <div className="grid gap-5 xl:grid-cols-[1.25fr_0.75fr]">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/40">
            Workspace overview
          </p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white md:text-4xl">
            Clean operational view for active pipeline work
          </h2>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-white/62 md:text-base">
            The workspace is now structured around one active run, fast stage
            execution, clear monitoring, and a review queue that is easier to
            scan, inspect, and moderate.
          </p>

          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            <div className="workspace-soft rounded-2xl p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-white/40">
                Active queue
              </p>
              <p className="mt-2 text-2xl font-semibold text-white">
                {activeQueueCount}
              </p>
            </div>

            <div className="workspace-soft rounded-2xl p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-white/40">
                Stale runs
              </p>
              <p className="mt-2 text-2xl font-semibold text-amber-300">
                {staleRunsCount}
              </p>
            </div>

            <div className="workspace-soft rounded-2xl p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-white/40">
                Review backlog
              </p>
              <p className="mt-2 text-2xl font-semibold text-cyan-200">
                {backlogCount}
              </p>
            </div>
          </div>
        </div>

        <div className="workspace-soft rounded-3xl p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/40">
            API connection
          </p>
          <p className="mt-3 text-2xl font-semibold text-white">{apiStatus}</p>
          <p className="mt-2 text-sm leading-6 text-white/60">{apiSubtitle}</p>

          <div className="mt-5 rounded-2xl border border-white/8 bg-white/[0.025] p-4">
            <p className="text-xs uppercase tracking-[0.16em] text-white/40">
              What changed in this step
            </p>
            <ul className="mt-3 space-y-2 text-sm leading-6 text-white/66">
              <li>Run-first workspace structure</li>
              <li>Cleaner information hierarchy</li>
              <li>More usable review moderation flow</li>
              <li>Reduced table heaviness and visual noise</li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}