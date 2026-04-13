type OverviewStatCardProps = {
  label: string;
  value: string | number;
  helper: string;
};

export function OverviewStatCard({
  label,
  value,
  helper,
}: OverviewStatCardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-widest text-slate-500">
        {label}
      </p>
      <p className="mt-3 text-2xl font-bold tracking-tight text-slate-900">
        {value}
      </p>
      <p className="mt-2 text-sm leading-5 text-slate-500">{helper}</p>
    </div>
  );
}
