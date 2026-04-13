type InfoTipProps = {
  title: string;
  description: string;
};

export function InfoTip({ title, description }: InfoTipProps) {
  return (
    <span className="group relative inline-flex align-middle">
      <button
        type="button"
        aria-label={title}
        className="inline-flex h-5 w-5 items-center justify-center rounded-full border border-slate-300 bg-slate-100 text-[11px] font-semibold text-slate-500 transition hover:border-blue-400 hover:bg-blue-50 hover:text-blue-600"
      >
        i
      </button>

      <span className="pointer-events-none absolute left-1/2 top-full z-20 mt-2 hidden w-64 -translate-x-1/2 rounded-xl border border-slate-200 bg-white px-3 py-3 text-left text-xs leading-5 text-slate-600 shadow-lg group-hover:block">
        <span className="block font-semibold text-slate-900">{title}</span>
        <span className="mt-1 block">{description}</span>
      </span>
    </span>
  );
}
