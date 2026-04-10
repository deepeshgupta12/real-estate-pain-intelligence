import { AppChip } from "@/components/ui/app-chip";

type HeroBannerProps = {
  apiStatus: string;
  apiSubtitle: string;
};

export function HeroBanner({ apiStatus, apiSubtitle }: HeroBannerProps) {
  return (
    <section className="relative overflow-hidden rounded-4xl border border-white/10 bg-white/5 p-8 shadow-[0_20px_70px_rgba(0,0,0,0.28)] backdrop-blur md:p-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(34,211,238,0.16),transparent_20%),radial-gradient(circle_at_left,rgba(59,130,246,0.12),transparent_30%)]" />
      <div className="relative">
        <div className="flex flex-wrap gap-2">
          <AppChip label="Phase 1" />
          <AppChip label="Step 3" />
          <AppChip label="Polished Frontend Shell" />
        </div>

        <div className="mt-6 max-w-4xl">
          <h2 className="text-4xl font-semibold leading-tight tracking-tight text-white md:text-5xl">
            Turn public real-estate pain points into product decisions.
          </h2>
          <p className="mt-5 max-w-3xl text-base leading-7 text-white/68 md:text-lg">
            This workspace will evolve into a multi-agent intelligence platform
            that captures public user complaints, maps them to journey stages,
            clusters recurring pain points, benchmarks competitors, and converts
            them into prioritized action recommendations for Square Yards.
          </p>
        </div>

        <div className="mt-8 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-3xl border border-white/10 bg-black/10 p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/45">
              Product intent
            </p>
            <p className="mt-3 text-sm leading-7 text-white/70">
              The final platform will support source ingestion, pipeline
              orchestration, multilingual normalization, pain-point extraction,
              clustering, prioritization, human review, Notion sync, and
              exportable reports including PDF outputs.
            </p>
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