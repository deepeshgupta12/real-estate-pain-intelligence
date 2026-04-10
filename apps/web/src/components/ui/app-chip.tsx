type AppChipProps = {
  label: string;
};

export function AppChip({ label }: AppChipProps) {
  return (
    <span className="inline-flex items-center rounded-full border border-cyan-400/25 bg-cyan-400/10 px-3 py-1 text-xs font-medium tracking-wide text-cyan-200">
      {label}
    </span>
  );
}