import { AppChip } from "@/components/ui/app-chip";

type TopbarProps = {
  environment: string;
  version: string;
  apiStatus: string;
};

export function Topbar({ environment, version, apiStatus }: TopbarProps) {
  return (
    <header className="sticky top-0 z-20 border-b border-white/10 bg-[#07111f]/70 backdrop-blur-xl">
      <div className="flex flex-col gap-4 px-5 py-4 lg:px-8 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/45">
            Real Estate Pain Point Intelligence Platform
          </p>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white">
            Product Intelligence Workspace
          </h1>
          <p className="mt-1 text-sm text-white/55">
            Build surface for scraping, analysis, prioritization, actioning, and
            reporting.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <AppChip label={`Env: ${environment}`} />
          <AppChip label={`Version: ${version}`} />
          <AppChip label={`API: ${apiStatus}`} />
        </div>
      </div>
    </header>
  );
}