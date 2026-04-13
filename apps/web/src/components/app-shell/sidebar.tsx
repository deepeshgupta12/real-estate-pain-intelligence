import { NavigationItem } from "@/types/navigation";

type SidebarProps = {
  items: NavigationItem[];
};

export function Sidebar({ items }: SidebarProps) {
  return (
    <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-slate-200 bg-white px-5 py-6 xl:flex">
      <div className="mb-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600 text-sm font-bold text-white">
            MI
          </div>

          <div>
            <p className="text-sm font-semibold text-slate-900">
              Market Intel
            </p>
            <p className="text-xs text-slate-500">Research console</p>
          </div>
        </div>
      </div>

      <nav className="space-y-1 flex-1">
        {items.map((item) => (
          <a
            key={item.id}
            href={item.href}
            className={`block rounded-lg px-4 py-2.5 transition text-sm ${
              item.active
                ? "bg-blue-50 text-blue-700 font-semibold"
                : "text-slate-700 hover:bg-slate-50"
            }`}
          >
            {item.label}
          </a>
        ))}
      </nav>

      <div className="border-t border-slate-200 pt-6">
        <a
          href="#settings"
          className="block rounded-lg px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition"
        >
          Settings
        </a>
        <p className="mt-3 text-xs text-slate-500">v1.0.0</p>
      </div>
    </aside>
  );
}