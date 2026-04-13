type SectionShellProps = {
  id?: string;
  eyebrow?: string;
  title: string;
  description: string;
  children: React.ReactNode;
};

export function SectionShell({
  id,
  eyebrow,
  title,
  description,
  children,
}: SectionShellProps) {
  return (
    <section
      id={id}
      className="rounded-4xl border border-white/10 bg-white/5 p-6 shadow-[0_18px_50px_rgba(0,0,0,0.18)]"
    >
      <div className="mb-5">
        {eyebrow ? (
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/45">
            {eyebrow}
          </p>
        ) : null}
        <h2 className="mt-2 text-2xl font-semibold tracking-tight text-white">
          {title}
        </h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-white/60">
          {description}
        </p>
      </div>

      {children}
    </section>
  );
}