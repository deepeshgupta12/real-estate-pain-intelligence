import { AppChip } from "@/components/ui/app-chip";

type TopbarProps = {
  environment: string;
  version: string;
  apiStatus: string;
};

export function Topbar({ environment, version, apiStatus }: TopbarProps) {
  return (
    <header className="sticky top-0 z-20 border-b border-white/8 bg-[#09111d]/82 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-4 lg:px-8 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-white/38">
            Real Estate Pain Point Intelligence Platform
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight text-white">
            Pipeline Operations Workspace
          </h1>
          <p className="mt-1 text-sm text-white/56">
            Operate runs, inspect health, and moderate output in one clean
            workspace.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <AppChip label={`Env: ${environment}`} />
          <AppChip label={`Version: ${version}`} />
          <AppChip label={`API: ${apiStatus}`} />
          <AppChip label="Step 26B.1 + 26B.2" />
        </div>
      </div>
    </header>
  );
}