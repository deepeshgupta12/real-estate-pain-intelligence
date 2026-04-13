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
    <section className="overflow-hidden rounded-xl border border-blue-100 bg-gradient-to-br from-blue-600 to-blue-700 p-6 shadow-md md:p-8">
      <div className="grid gap-6 xl:grid-cols-[1.4fr_0.6fr]">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-blue-200">
            Market Intelligence Console
          </p>
          <h2 className="mt-2 text-3xl font-bold tracking-tight text-white md:text-4xl">
            Find what&apos;s frustrating your customers
          </h2>
          <p className="mt-3 max-w-xl text-sm leading-7 text-blue-100 md:text-base">
            Collect real customer feedback from Reddit, YouTube, and app stores.
            Analyze pain points, review insights, and export reports — all in one place.
          </p>

          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            <div className="rounded-lg bg-white/10 p-4 backdrop-blur-sm">
              <p className="text-xs font-medium uppercase tracking-wide text-blue-200">
                Active Sessions
              </p>
              <p className="mt-2 text-2xl font-bold text-white">
                {activeQueueCount}
              </p>
            </div>

            <div className="rounded-lg bg-white/10 p-4 backdrop-blur-sm">
              <p className="text-xs font-medium uppercase tracking-wide text-blue-200">
                Stalled
              </p>
              <p className="mt-2 text-2xl font-bold text-amber-300">
                {staleRunsCount}
              </p>
            </div>

            <div className="rounded-lg bg-white/10 p-4 backdrop-blur-sm">
              <p className="text-xs font-medium uppercase tracking-wide text-blue-200">
                Review Backlog
              </p>
              <p className="mt-2 text-2xl font-bold text-cyan-200">
                {backlogCount}
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-xl bg-white/10 p-5 backdrop-blur-sm">
          <p className="text-xs font-semibold uppercase tracking-widest text-blue-200">
            API Status
          </p>
          <p className="mt-3 text-2xl font-bold text-white">{apiStatus}</p>
          <p className="mt-2 text-sm leading-6 text-blue-100">{apiSubtitle}</p>

          <div className="mt-5 rounded-lg border border-white/20 bg-white/5 p-4">
            <p className="text-xs font-semibold uppercase tracking-widest text-blue-200">
              6-Step Research Pipeline
            </p>
            <ul className="mt-3 space-y-2 text-sm leading-6 text-blue-100">
              <li>① Set up a research session</li>
              <li>② Collect posts from any platform</li>
              <li>③ Clean &amp; detect languages</li>
              <li>④ Analyze pain points automatically</li>
              <li>⑤ Review &amp; approve insights</li>
              <li>⑥ Export reports &amp; sync to Notion</li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
