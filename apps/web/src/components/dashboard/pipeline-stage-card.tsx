type PipelineStageCardProps = {
  step: string;
  title: string;
  description: string;
};

export function PipelineStageCard({
  step,
  title,
  description,
}: PipelineStageCardProps) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-200/75">
        {step}
      </p>
      <h3 className="mt-3 text-lg font-semibold text-white">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-white/60">{description}</p>
    </div>
  );
}