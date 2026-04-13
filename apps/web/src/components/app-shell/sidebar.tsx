import { NavigationItem } from "@/types/navigation";

type SidebarProps = {
  items: NavigationItem[];
};

export function Sidebar({ items }: SidebarProps) {
  return (
    <aside className="sticky top-0 hidden h-screen w-full max-w-76 shrink-0 flex-col border-r border-white/8 bg-[#08111b]/88 px-5 py-5 backdrop-blur xl:flex">
      <div className="workspace-surface rounded-3xl p-5">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-linear-to-br from-cyan-300 to-blue-500 text-sm font-bold text-slate-950">
            RE
          </div>

          <div>
            <p className="text-sm font-semibold text-white">
              Pain Intelligence
            </p>
            <p className="text-xs text-white/52">Operator workspace</p>
          </div>
        </div>

        <p className="mt-4 text-sm leading-6 text-white/62">
          Run the pipeline, inspect operational health, and validate generated
          output without switching between disconnected screens.
        </p>
      </div>

      <div className="mt-6">
        <p className="px-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-white/38">
          Workspace sections
        </p>
        <nav className="mt-3 space-y-2">
          {items.map((item) => (
            <a
              key={item.id}
              href={item.href}
              className={`block rounded-2xl border px-4 py-3 transition ${
                item.active
                  ? "border-cyan-400/24 bg-cyan-400/10"
                  : "border-white/8 bg-white/[0.025] hover:border-white/14 hover:bg-white/[0.04]"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p
                    className={`text-sm font-semibold ${
                      item.active ? "text-cyan-100" : "text-white"
                    }`}
                  >
                    {item.label}
                  </p>
                  <p className="mt-1 text-xs leading-5 text-white/48">
                    {item.description}
                  </p>
                </div>

                {item.badge ? (
                  <span className="badge badge-neutral shrink-0">
                    {item.badge}
                  </span>
                ) : null}
              </div>
            </a>
          ))}
        </nav>
      </div>

      <div className="mt-auto workspace-surface rounded-3xl p-4">
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/38">
          Current focus
        </p>
        <p className="mt-2 text-sm font-semibold text-white">
          Workspace UX reset
        </p>
        <p className="mt-2 text-sm leading-6 text-white/56">
          This step reduces clutter, strengthens operating flow, and rebuilds
          the review section into a more usable moderation workspace.
        </p>
      </div>
    </aside>
  );
}