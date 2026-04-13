"use client";

import { useState } from "react";
import { fetchRunEvents, RunEventResponse } from "@/lib/api";
import { SectionShell } from "@/components/console/section-shell";

type RunEventsPanelProps = {
  initialEvents: RunEventResponse[];
};

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
      eyebrow="Operational trace"
      title="Run events explorer"
      description="Filter recent events across runs or inspect a single run’s event stream by event type, stage, status, ordering, and limit."
    >
      <div className="grid gap-3 rounded-3xl border border-white/10 bg-black/10 p-4 md:grid-cols-2 xl:grid-cols-6">
        <input
          value={runId}
          onChange={(e) => setRunId(e.target.value)}
          placeholder="Run id"
          className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none placeholder:text-white/35"
        />
        <input
          value={eventType}
          onChange={(e) => setEventType(e.target.value)}
          placeholder="Event type"
          className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none placeholder:text-white/35"
        />
        <input
          value={stage}
          onChange={(e) => setStage(e.target.value)}
          placeholder="Stage"
          className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none placeholder:text-white/35"
        />
        <input
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          placeholder="Status"
          className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none placeholder:text-white/35"
        />
        <select
          value={newestFirst ? "true" : "false"}
          onChange={(e) => setNewestFirst(e.target.value === "true")}
          className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none"
        >
          <option value="true">Newest first</option>
          <option value="false">Oldest first</option>
        </select>
        <input
          value={limit}
          onChange={(e) => setLimit(e.target.value)}
          placeholder="Limit"
          className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none placeholder:text-white/35"
        />
      </div>

      <div className="mt-4 flex items-center gap-3">
        <button
          onClick={handleLoad}
          disabled={loading}
          className="rounded-2xl border border-cyan-400/30 bg-cyan-400/10 px-5 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-400/15 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Loading..." : "Load events"}
        </button>

        {error ? (
          <span className="text-sm text-red-200">{error}</span>
        ) : null}
      </div>

      <div className="mt-5 overflow-x-auto console-scrollbar">
        <table className="min-w-full border-separate border-spacing-y-2">
          <thead>
            <tr className="text-left text-xs uppercase tracking-[0.16em] text-white/45">
              <th className="px-4 py-2">ID</th>
              <th className="px-4 py-2">Run</th>
              <th className="px-4 py-2">Type</th>
              <th className="px-4 py-2">Stage</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Message</th>
              <th className="px-4 py-2">Created at</th>
            </tr>
          </thead>
          <tbody>
            {events.length === 0 ? (
              <tr>
                <td
                  colSpan={7}
                  className="rounded-2xl border border-white/10 bg-black/10 px-4 py-6 text-sm text-white/60"
                >
                  No events found for the selected filters.
                </td>
              </tr>
            ) : (
              events.map((event) => (
                <tr key={event.id} className="bg-white/5 text-sm text-white/72">
                  <td className="rounded-l-2xl px-4 py-3 font-medium text-white">
                    {event.id}
                  </td>
                  <td className="px-4 py-3">{event.scrape_run_id}</td>
                  <td className="px-4 py-3">{event.event_type}</td>
                  <td className="px-4 py-3">{event.stage}</td>
                  <td className="px-4 py-3">{event.status}</td>
                  <td className="px-4 py-3">{event.message}</td>
                  <td className="rounded-r-2xl px-4 py-3">{event.created_at}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </SectionShell>
  );
}