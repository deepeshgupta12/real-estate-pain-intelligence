import { QueueHealthItem } from "@/lib/api";
import { SectionShell } from "@/components/console/section-shell";

type QueueHealthPanelProps = {
  queueItems: QueueHealthItem[];
};

function humanize(value: string): string {
  return value.replaceAll("_", " ");
}

export function QueueHealthPanel({ queueItems }: QueueHealthPanelProps) {
  const activeCount = queueItems.filter((item) => item.status === "active").length;

  return (
    <SectionShell
      id="queue-health"
      eyebrow="System"
      title="Active Sessions"
      description="Monitor running research sessions"
    >
      {queueItems.length === 0 ? (
        <div className="rounded-lg bg-slate-50 px-6 py-8 text-center text-slate-600">
          No active sessions.
        </div>
      ) : (
        <div className="space-y-3">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-900">
              <span className="font-semibold">{activeCount}</span> session(s) running
            </p>
          </div>

          <div className="space-y-3">
            {queueItems.map((item) => (
              <div key={item.run_id} className="card p-4 flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-slate-900">Run #{item.run_id}</p>
                  <p className="text-sm text-slate-600 truncate">{item.brand_identifier}</p>
                </div>
                <div className="shrink-0 ml-4">
                  <span className="status-pill info">{humanize(item.status)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </SectionShell>
  );
}
