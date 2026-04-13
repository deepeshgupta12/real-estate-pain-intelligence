import { ReactNode } from "react";

type SectionCardProps = {
  title: string;
  description: string;
  children: ReactNode;
};

export function SectionCard({
  title,
  description,
  children,
}: SectionCardProps) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-5">
        <h2 className="text-xl font-semibold text-slate-900">{title}</h2>
        <p className="mt-1.5 max-w-3xl text-sm leading-6 text-slate-500">
          {description}
        </p>
      </div>
      {children}
    </section>
  );
}