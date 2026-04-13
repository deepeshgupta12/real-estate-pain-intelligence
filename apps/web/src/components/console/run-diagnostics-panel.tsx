"use client";

import { useState } from "react";
import { fetchRunDiagnostics, RunDiagnosticsResponse } from "@/lib/api";
import { SectionShell } from "@/components/console/section-shell";

type RunDiagnosticsPanelProps = {
  initialRunId: number | null;
  initialDiagnostics: RunDiagnosticsResponse | null;
};

export function RunDiagnosticsPanel({
  initialRunId,
  initialDiagnostics,
}: RunDiagnosticsPanelProps) {
  const [runId, setRunId] = useState(initialRunId ? String(initialRunId) : "");
  const [diagnostics, setDiagnostics] = useState<RunDiagnosticsResponse | null>(
    initialDiagnostics,
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLoad() {
    if (!runId.trim()) {
      setError("Enter a run id to inspect diagnostics.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const data = await fetchRunDiagnostics(Number(runId));
      setDiagnostics(data);
    } catch (err) {
      setDiagnostics(null);
      setError(err instanceof Error ? err.message : "Failed to load diagnostics");
    } finally {
      setLoading(false);
    }
  }

  return (
    <SectionShell
      id="run-diagnostics"
      eyebrow="Deep inspection"
      title="Run diagnostics"
      description="Inspect a run’s latest event, stage timeline, readiness snapshot, failure state, and stale-run metadata."
    >
      <div className="mb-5 flex flex-col gap-3 rounded-3xl border border-white/10 bg-black/10 p-4 md:flex-row md:items-end">
        <div className="min-w-0 flex-1">
          <label className="text-xs font-semibold uppercase tracking-[0.16em] text-white/45">
            Run ID
          </label>
          <input
            value={runId}
            onChange={(e) => setRunId(e.target.value)}
            placeholder="Enter run id"
            className="mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none placeholder:text-white/35"
          />
        </div>

        <button
          onClick={handleLoad}
          disabled={loading}
          className="rounded-2xl border border-cyan-400/30 bg-cyan-400/10 px-5 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-400/15 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Loading..." : "Load diagnostics"}
        </button>
      </div>

      {error ? (
        <div className="mb-5 rounded-2xl border border-red-400/20 bg-red-400/8 px-4 py-3 text-sm text-red-100">
          {error}
        </div>
      ) : null}

      {!diagnostics ? (
        <div className="rounded-2xl border border-white/10 bg-black/10 px-4 py-6 text-sm text-white/60">
          Load a run id to inspect diagnostics.
        </div>
      ) : (
        <div className="space-y-5">
          <div className="grid gap-4 lg:grid-cols-4">
            <div className="rounded-2xl border border-white/10 bg-black/10 p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-white/45">Status</p>
              <p className="mt-2 text-xl font-semibold text-white">
                {diagnostics.status}
              </p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-black/10 p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-white/45">Stage</p>
              <p className="mt-2 text-xl font-semibold text-white">
                {diagnostics.pipeline_stage}
              </p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-black/10 p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-white/45">Health</p>
              <p className="mt-2 text-xl font-semibold text-white">
                {diagnostics.health_label}
              </p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-black/10 p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-white/45">Events</p>
              <p className="mt-2 text-xl font-semibold text-white">
                {diagnostics.total_events}
              </p>
            </div>
          </div>

          <div className="grid gap-5 xl:grid-cols-2">
            <div className="rounded-3xl border border-white/10 bg-black/10 p-5">
              <h3 className="text-lg font-semibold text-white">Latest event</h3>
              <div className="mt-4 space-y-2 text-sm text-white/72">
                <p>
                  <span className="text-white/45">Type:</span>{" "}
                  {diagnostics.latest_event?.event_type ?? "N/A"}
                </p>
                <p>
                  <span className="text-white/45">Stage:</span>{" "}
                  {diagnostics.latest_event?.stage ?? "N/A"}
                </p>
                <p>
                  <span className="text-white/45">Status:</span>{" "}
                  {diagnostics.latest_event?.status ?? "N/A"}
                </p>
                <p>
                  <span className="text-white/45">Message:</span>{" "}
                  {diagnostics.latest_event?.message ?? "N/A"}
                </p>
                <p>
                  <span className="text-white/45">Created at:</span>{" "}
                  {diagnostics.latest_event?.created_at ?? "N/A"}
                </p>
              </div>
            </div>

            <div className="rounded-3xl border border-white/10 bg-black/10 p-5">
              <h3 className="text-lg font-semibold text-white">Failure snapshot</h3>
              <div className="mt-4 space-y-2 text-sm text-white/72">
                <p>
                  <span className="text-white/45">Failed:</span>{" "}
                  {diagnostics.failure_snapshot.failed ? "Yes" : "No"}
                </p>
                <p>
                  <span className="text-white/45">Error:</span>{" "}
                  {diagnostics.failure_snapshot.error_message ?? "N/A"}
                </p>
                <p>
                  <span className="text-white/45">Failed stage:</span>{" "}
                  {diagnostics.failure_snapshot.failed_stage ?? "N/A"}
                </p>
                <p>
                  <span className="text-white/45">Failed at:</span>{" "}
                  {diagnostics.failure_snapshot.failed_at ?? "N/A"}
                </p>
                <p>
                  <span className="text-white/45">Last successful stage:</span>{" "}
                  {diagnostics.failure_snapshot.last_successful_stage ?? "N/A"}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-white/10 bg-black/10 p-5">
            <h3 className="text-lg font-semibold text-white">Stage timeline</h3>
            <div className="mt-4 overflow-x-auto console-scrollbar">
              <table className="min-w-full border-separate border-spacing-y-2">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-[0.16em] text-white/45">
                    <th className="px-4 py-2">Stage</th>
                    <th className="px-4 py-2">First event</th>
                    <th className="px-4 py-2">Last event</th>
                    <th className="px-4 py-2">Latest status</th>
                    <th className="px-4 py-2">Events</th>
                    <th className="px-4 py-2">Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {diagnostics.stage_timeline.map((item) => (
                    <tr key={item.stage} className="bg-white/5 text-sm text-white/72">
                      <td className="rounded-l-2xl px-4 py-3 font-medium text-white">
                        {item.stage}
                      </td>
                      <td className="px-4 py-3">{item.first_event_at}</td>
                      <td className="px-4 py-3">{item.last_event_at}</td>
                      <td className="px-4 py-3">{item.latest_status}</td>
                      <td className="px-4 py-3">{item.event_count}</td>
                      <td className="rounded-r-2xl px-4 py-3">
                        {item.duration_seconds}s
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="grid gap-5 xl:grid-cols-2">
            <div className="rounded-3xl border border-white/10 bg-black/10 p-5">
              <h3 className="text-lg font-semibold text-white">Readiness checks</h3>
              <div className="mt-4 grid gap-2">
                {Object.entries(diagnostics.readiness_checks).map(([key, value]) => (
                  <div
                    key={key}
                    className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm"
                  >
                    <span className="text-white/70">{key}</span>
                    <span className={value ? "text-emerald-300" : "text-amber-300"}>
                      {String(value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-3xl border border-white/10 bg-black/10 p-5">
              <h3 className="text-lg font-semibold text-white">Readiness counts</h3>
              <div className="mt-4 grid gap-2">
                {Object.entries(diagnostics.readiness_counts).map(([key, value]) => (
                  <div
                    key={key}
                    className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm"
                  >
                    <span className="text-white/70">{key}</span>
                    <span className="text-white">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </SectionShell>
  );
}