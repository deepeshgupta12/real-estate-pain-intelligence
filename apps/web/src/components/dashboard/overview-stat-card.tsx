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
    <div className="workspace-surface rounded-3xl p-5">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-white/40">
        {label}
      </p>
      <p className="mt-3 text-2xl font-semibold tracking-tight text-white">
        {value}
      </p>
      <p className="mt-2 text-sm leading-6 text-white/56">{helper}</p>
    </div>
  );
}