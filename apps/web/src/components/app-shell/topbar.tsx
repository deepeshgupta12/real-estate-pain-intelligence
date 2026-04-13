type TopbarProps = {
  environment: string;
  version: string;
  apiStatus: string;
};

export function Topbar({ environment, version, apiStatus }: TopbarProps) {
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-7xl flex-col gap-2 px-5 py-4 lg:px-8 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
            Market Intelligence
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Real estate customer pain point analytics
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="inline-flex items-center gap-2 rounded-full bg-green-50 px-3 py-1.5 text-sm">
            <span className="inline-block h-2 w-2 rounded-full bg-green-600"></span>
            <span className="text-green-700 font-medium">Connected</span>
          </div>
        </div>
      </div>
    </header>
  );
}