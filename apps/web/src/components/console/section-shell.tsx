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
    <section id={id} className="workspace-surface rounded-4xl p-6 md:p-7">
      <div className="mb-6">
        {eyebrow ? (
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/38">
            {eyebrow}
          </p>
        ) : null}
        <h2 className="mt-2 text-2xl font-semibold tracking-tight text-white">
          {title}
        </h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-white/58">
          {description}
        </p>
      </div>

      {children}
    </section>
  );
}