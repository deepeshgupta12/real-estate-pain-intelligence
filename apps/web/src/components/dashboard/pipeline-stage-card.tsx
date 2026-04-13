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
    <div className="workspace-surface rounded-3xl p-5">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-200/75">
        {step}
      </p>
      <h3 className="mt-2 text-lg font-semibold text-white">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-white/58">{description}</p>
    </div>
  );
}