import { QueueHealthItem } from "@/lib/api";
import { SectionShell } from "@/components/console/section-shell";

type QueueHealthPanelProps = {
  queueItems: QueueHealthItem[];
};

function healthClass(healthLabel: string): string {
  if (healthLabel === "healthy") return "badge badge-success";
  if (healthLabel === "stale") return "badge badge-warning";
  if (healthLabel === "failed") return "badge badge-danger";
  return "badge badge-neutral";
}

function humanize(value: string | null | undefined): string {
  if (!value) return "N/A";
  return value.replaceAll("_", " ");
}

export function QueueHealthPanel({ queueItems }: QueueHealthPanelProps) {
  return (
    <SectionShell
      id="queue-health"
      eyebrow="Monitoring"
      title="Queue health"
      description="See active runs, heartbeat freshness, current stage, and the latest event snapshot without the older heavy table treatment."
    >
      <div className="workspace-soft rounded-3xl overflow-hidden">
        <div className="overflow-x-auto console-scrollbar">
          <table className="data-table min-w-225">
            <thead>
              <tr>
                <th>Run</th>
                <th>Source</th>
                <th>Brand</th>
                <th>Stage</th>
                <th>Health</th>
                <th>Heartbeat</th>
                <th>Latest event</th>
              </tr>
            </thead>
            <tbody>
              {queueItems.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-6 text-sm text-white/58">
                    No active runs are currently present in the queue.
                  </td>
                </tr>
              ) : (
                queueItems.map((item) => (
                  <tr key={item.run_id} className="data-row-hover">
                    <td className="font-semibold text-white">#{item.run_id}</td>
                    <td>{humanize(item.source_name)}</td>
                    <td>{item.target_brand}</td>
                    <td>
                      <div className="font-medium text-white">
                        {humanize(item.pipeline_stage)}
                      </div>
                      <div className="mt-1 text-xs text-white/45">
                        {humanize(item.status)}
                      </div>
                    </td>
                    <td>
                      <span className={healthClass(item.health_label)}>
                        {humanize(item.health_label)}
                      </span>
                    </td>
                    <td>
                      <div>{item.heartbeat_age_seconds ?? "N/A"}s ago</div>
                      <div className="mt-1 text-xs text-white/45">
                        {item.last_heartbeat_at ?? "N/A"}
                      </div>
                    </td>
                    <td>
                      <div className="font-medium text-white">
                        {humanize(item.latest_event_type)}
                      </div>
                      <div className="mt-1 max-w-md text-xs leading-5 text-white/50">
                        {item.latest_event_message ?? "No event message available"}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </SectionShell>
  );
}