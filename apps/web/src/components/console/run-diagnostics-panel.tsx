"use client";

import { useState } from "react";
import { fetchRunDiagnostics, RunDiagnosticsResponse } from "@/lib/api";
import { SectionShell } from "@/components/console/section-shell";

type RunDiagnosticsPanelProps = {
  initialRunId: number | null;
  initialDiagnostics: RunDiagnosticsResponse | null;
};

function humanize(value: string | null | undefined): string {
  if (!value) return "N/A";
  return value.replaceAll("_", " ");
}

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
      eyebrow="Inspection"
      title="Run diagnostics"
      description="Inspect stage flow, latest event, readiness shape, and failure state for one run."
    >
      <div className="workspace-soft mb-5 rounded-3xl p-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-end">
          <div className="min-w-0 flex-1">
            <label className="text-xs font-semibold uppercase tracking-[0.16em] text-white/40">
              Run ID
            </label>
            <input
              value={runId}
              onChange={(e) => setRunId(e.target.value)}
              placeholder="Enter run id"
              className="field-shell mt-2 w-full rounded-2xl px-4 py-3 text-sm"
            />
          </div>

          <button
            onClick={handleLoad}
            disabled={loading}
            className="rounded-2xl border border-cyan-400/28 bg-cyan-400/12 px-5 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-400/18 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Loading..." : "Load diagnostics"}
          </button>
        </div>
      </div>

      {error ? (
        <div className="mb-5 rounded-2xl border border-red-400/18 bg-red-400/10 px-4 py-3 text-sm text-red-100">
          {error}
        </div>
      ) : null}

      {!diagnostics ? (
        <div className="workspace-soft rounded-2xl px-4 py-6 text-sm text-white/58">
          Load a run id to inspect diagnostics.
        </div>
      ) : (
        <div className="space-y-5">
          <div className="grid gap-4 lg:grid-cols-4">
            <div className="workspace-soft rounded-2xl p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-white/40">Status</p>
              <p className="mt-2 text-xl font-semibold text-white">
                {humanize(diagnostics.status)}
              </p>
            </div>
            <div className="workspace-soft rounded-2xl p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-white/40">Stage</p>
              <p className="mt-2 text-xl font-semibold text-white">
                {humanize(diagnostics.pipeline_stage)}
              </p>
            </div>
            <div className="workspace-soft rounded-2xl p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-white/40">Health</p>
              <p className="mt-2 text-xl font-semibold text-white">
                {humanize(diagnostics.health_label)}
              </p>
            </div>
            <div className="workspace-soft rounded-2xl p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-white/40">Events</p>
              <p className="mt-2 text-xl font-semibold text-white">
                {diagnostics.total_events}
              </p>
            </div>
          </div>

          <div className="grid gap-5 xl:grid-cols-2">
            <div className="workspace-soft rounded-3xl p-5">
              <h3 className="text-lg font-semibold text-white">Latest event</h3>
              <div className="mt-4 grid gap-3">
                <div className="rounded-2xl border border-white/8 bg-white/2 px-4 py-3 text-sm text-white/76">
                  <span className="text-white/40">Type:</span>{" "}
                  {humanize(diagnostics.latest_event?.event_type)}
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/2 px-4 py-3 text-sm text-white/76">
                  <span className="text-white/40">Stage:</span>{" "}
                  {humanize(diagnostics.latest_event?.stage)}
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/2 px-4 py-3 text-sm text-white/76">
                  <span className="text-white/40">Status:</span>{" "}
                  {humanize(diagnostics.latest_event?.status)}
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/2 px-4 py-3 text-sm text-white/76">
                  <span className="text-white/40">Message:</span>{" "}
                  {diagnostics.latest_event?.message ?? "N/A"}
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/2 px-4 py-3 text-sm text-white/76">
                  <span className="text-white/40">Created at:</span>{" "}
                  {diagnostics.latest_event?.created_at ?? "N/A"}
                </div>
              </div>
            </div>

            <div className="workspace-soft rounded-3xl p-5">
              <h3 className="text-lg font-semibold text-white">Failure snapshot</h3>
              <div className="mt-4 grid gap-3">
                <div className="rounded-2xl border border-white/8 bg-white/2 px-4 py-3 text-sm text-white/76">
                  <span className="text-white/40">Failed:</span>{" "}
                  {diagnostics.failure_snapshot.failed ? "Yes" : "No"}
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/2 px-4 py-3 text-sm text-white/76">
                  <span className="text-white/40">Error:</span>{" "}
                  {diagnostics.failure_snapshot.error_message ?? "N/A"}
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/2 px-4 py-3 text-sm text-white/76">
                  <span className="text-white/40">Failed stage:</span>{" "}
                  {humanize(diagnostics.failure_snapshot.failed_stage)}
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/2 px-4 py-3 text-sm text-white/76">
                  <span className="text-white/40">Failed at:</span>{" "}
                  {diagnostics.failure_snapshot.failed_at ?? "N/A"}
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/2 px-4 py-3 text-sm text-white/76">
                  <span className="text-white/40">Last successful stage:</span>{" "}
                  {humanize(diagnostics.failure_snapshot.last_successful_stage)}
                </div>
              </div>
            </div>
          </div>

          <div className="workspace-soft rounded-3xl p-5">
            <h3 className="text-lg font-semibold text-white">Stage timeline</h3>
            <div className="mt-4 overflow-x-auto console-scrollbar">
              <table className="data-table min-w-225">
                <thead>
                  <tr>
                    <th>Stage</th>
                    <th>First event</th>
                    <th>Last event</th>
                    <th>Latest status</th>
                    <th>Events</th>
                    <th>Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {diagnostics.stage_timeline.map((item) => (
                    <tr key={item.stage} className="data-row-hover">
                      <td className="font-medium text-white">
                        {humanize(item.stage)}
                      </td>
                      <td>{item.first_event_at}</td>
                      <td>{item.last_event_at}</td>
                      <td>{humanize(item.latest_status)}</td>
                      <td>{item.event_count}</td>
                      <td>{item.duration_seconds}s</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="grid gap-5 xl:grid-cols-2">
            <div className="workspace-soft rounded-3xl p-5">
              <h3 className="text-lg font-semibold text-white">Readiness checks</h3>
              <div className="mt-4 grid gap-2">
                {Object.entries(diagnostics.readiness_checks).map(([key, value]) => (
                  <div
                    key={key}
                    className="flex items-center justify-between rounded-2xl border border-white/8 bg-white/2 px-4 py-3 text-sm"
                  >
                    <span className="text-white/70">{humanize(key)}</span>
                    <span className={value ? "text-emerald-300" : "text-amber-300"}>
                      {String(value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="workspace-soft rounded-3xl p-5">
              <h3 className="text-lg font-semibold text-white">Readiness counts</h3>
              <div className="mt-4 grid gap-2">
                {Object.entries(diagnostics.readiness_counts).map(([key, value]) => (
                  <div
                    key={key}
                    className="flex items-center justify-between rounded-2xl border border-white/8 bg-white/2 px-4 py-3 text-sm"
                  >
                    <span className="text-white/70">{humanize(key)}</span>
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