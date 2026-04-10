import { NavigationItem } from "@/types/navigation";

type SidebarProps = {
  items: NavigationItem[];
};

export function Sidebar({ items }: SidebarProps) {
  return (
    <aside className="sticky top-0 hidden h-screen w-full max-w-70 flex-col border-r border-white/10 bg-black/10 px-5 py-6 backdrop-blur xl:flex">
      <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-linear-to-br from-cyan-400 to-blue-500 text-sm font-bold text-slate-950">
            RE
          </div>
          <div>
            <p className="text-sm font-semibold text-white">
              Pain Intelligence
            </p>
            <p className="text-xs text-white/55">Web Command Center</p>
          </div>
        </div>

        <p className="mt-4 text-sm leading-6 text-white/65">
          Public Voice-of-Customer intelligence platform for Indian real-estate
          brands and competitive product analysis.
        </p>
      </div>

      <nav className="mt-6 space-y-2">
        {items.map((item) => (
          <div
            key={item.label}
            className={`rounded-2xl border px-4 py-4 transition ${
              item.active
                ? "border-cyan-400/30 bg-cyan-400/10 shadow-[0_12px_40px_rgba(34,211,238,0.08)]"
                : "border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/7"
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p
                  className={`text-sm font-semibold ${
                    item.active ? "text-cyan-100" : "text-white"
                  }`}
                >
                  {item.label}
                </p>
                <p className="mt-1 text-xs leading-5 text-white/55">
                  {item.description}
                </p>
              </div>

              {item.badge ? (
                <span className="rounded-full border border-white/10 bg-black/20 px-2 py-1 text-[10px] font-medium uppercase tracking-wide text-white/60">
                  {item.badge}
                </span>
              ) : null}
            </div>
          </div>
        ))}
      </nav>

      <div className="mt-auto rounded-3xl border border-white/10 bg-white/5 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/45">
          Current stage
        </p>
        <p className="mt-3 text-sm font-semibold text-white">
          Frontend shell foundation
        </p>
        <p className="mt-2 text-sm leading-6 text-white/55">
          Building the polished dashboard chrome and reusable UI structure
          before feature modules are added.
        </p>
      </div>
    </aside>
  );
}