type StatusCardProps = {
  title: string;
  value: string;
  subtitle: string;
};

export function StatusCard({ title, value, subtitle }: StatusCardProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-[0_10px_30px_rgba(0,0,0,0.25)] backdrop-blur">
      <p className="text-sm font-medium text-white/70">{title}</p>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-white">{value}</p>
      <p className="mt-2 text-sm text-white/60">{subtitle}</p>
    </div>
  );
}