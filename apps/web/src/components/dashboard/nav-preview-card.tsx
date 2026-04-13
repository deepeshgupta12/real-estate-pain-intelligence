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
    <section className="workspace-surface rounded-3xl p-6">
      <div>
        <h3 className="text-lg font-semibold text-white">{title}</h3>
        <p className="mt-2 text-sm leading-6 text-white/60">{description}</p>
      </div>

      <div className="mt-5 space-y-2">
        {points.map((point) => (
          <div
            key={point}
            className="workspace-soft rounded-2xl px-4 py-3 text-sm leading-6 text-white/74"
          >
            {point}
          </div>
        ))}
      </div>
    </section>
  );
}