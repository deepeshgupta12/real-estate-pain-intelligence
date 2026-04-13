"use client";

import { useState } from "react";
import { fetchRunEvents, RunEventResponse } from "@/lib/api";
import { SectionShell } from "@/components/console/section-shell";

type RunEventsPanelProps = {
  initialEvents: RunEventResponse[];
};

function humanize(value: string | null | undefined): string {
  if (!value) return "N/A";
  return value.replaceAll("_", " ");
}

export function RunEventsPanel({ initialEvents }: RunEventsPanelProps) {
  const [runId, setRunId] = useState("");
  const [eventType, setEventType] = useState("");
  const [stage, setStage] = useState("");
  const [status, setStatus] = useState("");
  const [newestFirst, setNewestFirst] = useState(true);
  const [limit, setLimit] = useState("20");
  const [events, setEvents] = useState<RunEventResponse[]>(initialEvents);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLoad() {
    setLoading(true);
    setError("");

    try {
      const data = await fetchRunEvents({
        runId: runId ? Number(runId) : undefined,
        eventType: eventType || undefined,
        stage: stage || undefined,
        status: status || undefined,
        newestFirst,
        limit: Number(limit),
        offset: 0,
      });
      setEvents(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load events");
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <SectionShell
      id="run-events"
      eyebrow="Event stream"
      title="Run events explorer"
      description="Filter events with a simpler layout and a more readable event table."
    >
      <div className="workspace-soft rounded-3xl p-4">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
          <input
            value={runId}
            onChange={(e) => setRunId(e.target.value)}
            placeholder="Run id"
            className="field-shell rounded-2xl px-4 py-3 text-sm"
          />
          <input
            value={eventType}
            onChange={(e) => setEventType(e.target.value)}
            placeholder="Event type"
            className="field-shell rounded-2xl px-4 py-3 text-sm"
          />
          <input
            value={stage}
            onChange={(e) => setStage(e.target.value)}
            placeholder="Stage"
            className="field-shell rounded-2xl px-4 py-3 text-sm"
          />
          <input
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            placeholder="Status"
            className="field-shell rounded-2xl px-4 py-3 text-sm"
          />
          <select
            value={newestFirst ? "true" : "false"}
            onChange={(e) => setNewestFirst(e.target.value === "true")}
            className="field-shell rounded-2xl px-4 py-3 text-sm"
          >
            <option value="true">Newest first</option>
            <option value="false">Oldest first</option>
          </select>
          <input
            value={limit}
            onChange={(e) => setLimit(e.target.value)}
            placeholder="Limit"
            className="field-shell rounded-2xl px-4 py-3 text-sm"
          />
        </div>

        <div className="mt-4 flex items-center gap-3">
          <button
            onClick={handleLoad}
            disabled={loading}
            className="rounded-2xl border border-cyan-400/28 bg-cyan-400/12 px-5 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-400/18 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Loading..." : "Load events"}
          </button>

          {error ? (
            <span className="text-sm text-red-200">{error}</span>
          ) : null}
        </div>
      </div>

      <div className="workspace-soft mt-5 rounded-3xl overflow-hidden">
        <div className="overflow-x-auto console-scrollbar">
          <table className="data-table min-w-245">
            <thead>
              <tr>
                <th>ID</th>
                <th>Run</th>
                <th>Type</th>
                <th>Stage</th>
                <th>Status</th>
                <th>Message</th>
                <th>Created at</th>
              </tr>
            </thead>
            <tbody>
              {events.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-6 text-sm text-white/58">
                    No events found for the selected filters.
                  </td>
                </tr>
              ) : (
                events.map((event) => (
                  <tr key={event.id} className="data-row-hover">
                    <td className="font-medium text-white">{event.id}</td>
                    <td>{event.scrape_run_id}</td>
                    <td>{humanize(event.event_type)}</td>
                    <td>{humanize(event.stage)}</td>
                    <td>{humanize(event.status)}</td>
                    <td className="max-w-xl">{event.message}</td>
                    <td>{event.created_at}</td>
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