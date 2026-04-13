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
        className="inline-flex h-5 w-5 items-center justify-center rounded-full border border-white/14 bg-white/[0.04] text-[11px] font-semibold text-white/65 transition hover:border-cyan-300/35 hover:text-cyan-100"
      >
        i
      </button>

      <span className="pointer-events-none absolute left-1/2 top-full z-20 mt-2 hidden w-64 -translate-x-1/2 rounded-2xl border border-white/10 bg-[#0d1726] px-3 py-3 text-left text-xs leading-5 text-white/78 shadow-[0_18px_50px_rgba(0,0,0,0.35)] group-hover:block">
        <span className="block font-semibold text-white">{title}</span>
        <span className="mt-1 block">{description}</span>
      </span>
    </span>
  );
}