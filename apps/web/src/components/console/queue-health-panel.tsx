import { QueueHealthItem } from "@/lib/api";
import { SectionShell } from "@/components/console/section-shell";

type QueueHealthPanelProps = {
  queueItems: QueueHealthItem[];
};

function healthTone(healthLabel: string): string {
  if (healthLabel === "healthy") {
    return "text-emerald-300";
  }
  if (healthLabel === "stale") {
    return "text-amber-300";
  }
  if (healthLabel === "failed") {
    return "text-red-300";
  }
  return "text-white";
}

export function QueueHealthPanel({ queueItems }: QueueHealthPanelProps) {
  return (
    <SectionShell
      id="queue-health"
      eyebrow="Operational monitoring"
      title="Queue health"
      description="Live active-run queue with heartbeat freshness, latest event snapshot, and health labeling."
    >
      <div className="overflow-x-auto console-scrollbar">
        <table className="min-w-full border-separate border-spacing-y-2">
          <thead>
            <tr className="text-left text-xs uppercase tracking-[0.16em] text-white/45">
              <th className="px-4 py-2">Run</th>
              <th className="px-4 py-2">Source</th>
              <th className="px-4 py-2">Brand</th>
              <th className="px-4 py-2">Stage</th>
              <th className="px-4 py-2">Health</th>
              <th className="px-4 py-2">Heartbeat</th>
              <th className="px-4 py-2">Latest event</th>
            </tr>
          </thead>
          <tbody>
            {queueItems.length === 0 ? (
              <tr>
                <td
                  colSpan={7}
                  className="rounded-2xl border border-white/10 bg-black/10 px-4 py-6 text-sm text-white/60"
                >
                  No active runs are currently present in the queue.
                </td>
              </tr>
            ) : (
              queueItems.map((item) => (
                <tr
                  key={item.run_id}
                  className="rounded-2xl border border-white/10 bg-black/10 text-sm text-white/75"
                >
                  <td className="rounded-l-2xl px-4 py-4 font-semibold text-white">
                    {item.run_id}
                  </td>
                  <td className="px-4 py-4">{item.source_name}</td>
                  <td className="px-4 py-4">{item.target_brand}</td>
                  <td className="px-4 py-4">
                    <div className="font-medium text-white">{item.pipeline_stage}</div>
                    <div className="mt-1 text-xs text-white/50">{item.status}</div>
                  </td>
                  <td className={`px-4 py-4 font-semibold ${healthTone(item.health_label)}`}>
                    {item.health_label}
                  </td>
                  <td className="px-4 py-4">
                    <div>{item.heartbeat_age_seconds}s ago</div>
                    <div className="mt-1 text-xs text-white/50">
                      {item.last_heartbeat_at ?? "N/A"}
                    </div>
                  </td>
                  <td className="rounded-r-2xl px-4 py-4">
                    <div className="font-medium text-white">
                      {item.latest_event_type ?? "N/A"}
                    </div>
                    <div className="mt-1 max-w-md text-xs leading-5 text-white/55">
                      {item.latest_event_message ?? "No event message available"}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </SectionShell>
  );
}