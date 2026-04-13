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
    <section id={id} className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm md:p-7">
      <div className="mb-6">
        {eyebrow ? (
          <p className="text-[11px] font-semibold uppercase tracking-widest text-blue-600">
            {eyebrow}
          </p>
        ) : null}
        <h2 className="mt-1 text-xl font-semibold tracking-tight text-slate-900">
          {title}
        </h2>
        <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-500">
          {description}
        </p>
      </div>

      {children}
    </section>
  );
}