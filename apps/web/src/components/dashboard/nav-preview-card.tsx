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
    <section className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-[0_16px_50px_rgba(0,0,0,0.18)]">
      <div>
        <h3 className="text-xl font-semibold text-white">{title}</h3>
        <p className="mt-2 text-sm leading-6 text-white/62">{description}</p>
      </div>

      <div className="mt-5 space-y-3">
        {points.map((point) => (
          <div
            key={point}
            className="rounded-2xl border border-white/10 bg-black/10 px-4 py-3 text-sm text-white/72"
          >
            {point}
          </div>
        ))}
      </div>
    </section>
  );
}