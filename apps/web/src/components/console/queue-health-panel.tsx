import { QueueHealthItem } from "@/lib/api";

type QueueHealthPanelProps = {
  queueItems: QueueHealthItem[];
};

const STATUS_STYLES: Record<string, string> = {
  running:    "bg-green-50 text-green-700 border-green-200",
  active:     "bg-green-50 text-green-700 border-green-200",
  queued:     "bg-blue-50 text-blue-700 border-blue-200",
  pending:    "bg-amber-50 text-amber-700 border-amber-200",
  failed:     "bg-red-50 text-red-700 border-red-200",
  completed:  "bg-slate-50 text-slate-600 border-slate-200",
};

export function QueueHealthPanel({ queueItems }: QueueHealthPanelProps) {
  const activeCount = queueItems.filter(
    (i) => i.status === "active" || i.status === "running",
  ).length;

  return (
    <section id="queue-health" className="card p-5">
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-widest text-blue-600">System</p>
          <h2 className="text-base font-semibold text-slate-900">Active Sessions</h2>
        </div>
        <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">
          {activeCount} running · {queueItems.length} total
        </span>
      </div>

      {queueItems.length === 0 ? (
        <p className="text-sm text-slate-400 text-center py-4">No active sessions.</p>
      ) : (
        <div className="overflow-hidden rounded-lg border border-slate-200">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-left">
                <th className="px-4 py-2 text-xs font-semibold text-slate-500">Run</th>
                <th className="px-4 py-2 text-xs font-semibold text-slate-500">Brand</th>
                <th className="px-4 py-2 text-xs font-semibold text-slate-500">Source</th>
                <th className="px-4 py-2 text-xs font-semibold text-slate-500 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {queueItems.map((item) => {
                const style = STATUS_STYLES[item.status] ?? "bg-slate-50 text-slate-600 border-slate-200";
                return (
                  <tr key={item.run_id} className="hover:bg-slate-50 transition">
                    <td className="px-4 py-2 font-medium text-slate-900">#{item.run_id}</td>
                    <td className="px-4 py-2 text-slate-700 max-w-[140px] truncate">{item.target_brand}</td>
                    <td className="px-4 py-2 text-slate-500">{item.source_name}</td>
                    <td className="px-4 py-2 text-right">
                      <span className={`inline-block rounded-full border px-2.5 py-0.5 text-xs font-semibold capitalize ${style}`}>
                        {item.status.replaceAll("_", " ")}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
