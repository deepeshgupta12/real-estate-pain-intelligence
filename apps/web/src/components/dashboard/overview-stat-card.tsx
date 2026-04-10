type OverviewStatCardProps = {
  label: string;
  value: string;
  helper: string;
};

export function OverviewStatCard({
  label,
  value,
  helper,
}: OverviewStatCardProps) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-[0_14px_36px_rgba(0,0,0,0.18)]">
      <p className="text-sm font-medium text-white/58">{label}</p>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-white">
        {value}
      </p>
      <p className="mt-2 text-sm leading-6 text-white/55">{helper}</p>
    </div>
  );
}