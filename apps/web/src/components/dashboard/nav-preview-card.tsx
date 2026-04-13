type NavPreviewCardProps = {
  title: string;
  description: string;
  points: string[];
};

export function NavPreviewCard({
  title,
  description,
  points,
}: NavPreviewCardProps) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div>
        <h3 className="text-base font-semibold text-slate-900">{title}</h3>
        <p className="mt-1 text-sm leading-6 text-slate-500">{description}</p>
      </div>

      <div className="mt-4 space-y-2">
        {points.map((point) => (
          <div
            key={point}
            className="rounded-lg bg-slate-50 px-4 py-2.5 text-sm leading-6 text-slate-700"
          >
            {point}
          </div>
        ))}
      </div>
    </section>
  );
}
