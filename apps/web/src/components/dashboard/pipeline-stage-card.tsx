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
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-widest text-blue-600">
        {step}
      </p>
      <h3 className="mt-2 text-base font-semibold text-slate-900">{title}</h3>
      <p className="mt-1.5 text-sm leading-6 text-slate-500">{description}</p>
    </div>
  );
}
