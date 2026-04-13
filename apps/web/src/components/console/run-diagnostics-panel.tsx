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

function statusColor(value: string | null | undefined): string {
  if (!value) return "text-slate-500";
  const v = value.toLowerCase();
  if (v === "completed" || v === "healthy") return "text-green-600";
  if (v === "failed" || v === "error") return "text-red-600";
  if (v === "running" || v === "active") return "text-blue-600";
  if (v === "stale") return "text-amber-600";
  return "text-slate-700";
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
      setError("Please enter a session ID to inspect.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const data = await fetchRunDiagnostics(Number(runId));
      setDiagnostics(data);
    } catch (err) {
      setDiagnostics(null);
      setError(err instanceof Error ? err.message : "Failed to load session details");
    } finally {
      setLoading(false);
    }
  }

  return (
    <SectionShell
      id="run-diagnostics"
      eyebrow="Inspection"
      title="Session Details"
      description="Inspect stage flow, latest event, readiness, and failure state for any session."
    >
      {/* Filter bar */}
      <div className="mb-5 rounded-lg border border-slate-200 bg-slate-50 p-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-end">
          <div className="min-w-0 flex-1">
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1.5">
              Session ID
            </label>
            <input
              value={runId}
              onChange={(e) => setRunId(e.target.value)}
              placeholder="Enter session ID (e.g. 131)"
              className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <button
            onClick={handleLoad}
            disabled={loading}
            className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "Loading…" : "Load Details"}
          </button>
        </div>
      </div>

      {error ? (
        <div className="mb-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      {!diagnostics ? (
        <div className="rounded-lg bg-slate-50 px-6 py-10 text-center text-sm text-slate-500">
          Enter a session ID above to inspect its details.
        </div>
      ) : (
        <div className="space-y-5">
          {/* Status strip */}
          <div className="grid gap-4 lg:grid-cols-4">
            {[
              { label: "Status", value: diagnostics.status },
              { label: "Current Step", value: diagnostics.pipeline_stage },
              { label: "Health", value: diagnostics.health_label },
              { label: "Total Events", value: String(diagnostics.total_events) },
            ].map(({ label, value }) => (
              <div key={label} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
                <p className={`mt-2 text-lg font-bold capitalize ${statusColor(value)}`}>
                  {humanize(value)}
                </p>
              </div>
            ))}
          </div>

          {/* Latest event + Failure snapshot */}
          <div className="grid gap-5 xl:grid-cols-2">
            <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-base font-semibold text-slate-900">Latest Event</h3>
              <div className="mt-4 space-y-2">
                {[
                  { label: "Type", value: humanize(diagnostics.latest_event?.event_type) },
                  { label: "Stage", value: humanize(diagnostics.latest_event?.stage) },
                  { label: "Status", value: humanize(diagnostics.latest_event?.status) },
                  { label: "Message", value: diagnostics.latest_event?.message ?? "N/A" },
                  { label: "When", value: diagnostics.latest_event?.created_at ?? "N/A" },
                ].map(({ label, value }) => (
                  <div key={label} className="flex items-start gap-2 rounded-md bg-slate-50 px-3 py-2 text-sm">
                    <span className="shrink-0 font-medium text-slate-500 w-16">{label}</span>
                    <span className="text-slate-800 break-all">{value}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-base font-semibold text-slate-900">Failure Snapshot</h3>
              <div className="mt-4 space-y-2">
                {[
                  { label: "Failed", value: diagnostics.failure_snapshot.failed ? "Yes" : "No" },
                  { label: "Error", value: diagnostics.failure_snapshot.error_message ?? "None" },
                  { label: "Stage", value: humanize(diagnostics.failure_snapshot.failed_stage) },
                  { label: "At", value: diagnostics.failure_snapshot.failed_at ?? "N/A" },
                  { label: "Last OK", value: humanize(diagnostics.failure_snapshot.last_successful_stage) },
                ].map(({ label, value }) => (
                  <div key={label} className="flex items-start gap-2 rounded-md bg-slate-50 px-3 py-2 text-sm">
                    <span className="shrink-0 font-medium text-slate-500 w-16">{label}</span>
                    <span className={`break-all ${label === "Failed" && value === "Yes" ? "text-red-600 font-semibold" : "text-slate-800"}`}>{value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Stage timeline */}
          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-base font-semibold text-slate-900 mb-4">Stage Timeline</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200">
                    {["Stage", "First Event", "Last Event", "Latest Status", "Events", "Duration"].map((h) => (
                      <th key={h} className="pb-2 pr-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {diagnostics.stage_timeline.map((item) => (
                    <tr key={item.stage} className="hover:bg-slate-50">
                      <td className="py-2.5 pr-4 font-medium text-slate-900 capitalize">{humanize(item.stage)}</td>
                      <td className="py-2.5 pr-4 text-slate-500">{item.first_event_at}</td>
                      <td className="py-2.5 pr-4 text-slate-500">{item.last_event_at}</td>
                      <td className={`py-2.5 pr-4 capitalize font-medium ${statusColor(item.latest_status)}`}>{humanize(item.latest_status)}</td>
                      <td className="py-2.5 pr-4 text-slate-700">{item.event_count}</td>
                      <td className="py-2.5 text-slate-700">{item.duration_seconds}s</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Readiness */}
          <div className="grid gap-5 xl:grid-cols-2">
            <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-base font-semibold text-slate-900 mb-4">Readiness Checks</h3>
              <div className="space-y-2">
                {Object.entries(diagnostics.readiness_checks).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between rounded-md bg-slate-50 px-3 py-2 text-sm">
                    <span className="text-slate-600 capitalize">{humanize(key)}</span>
                    <span className={`font-semibold ${value ? "text-green-600" : "text-amber-600"}`}>
                      {value ? "✓ Ready" : "⚠ Not yet"}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-base font-semibold text-slate-900 mb-4">Stage Counts</h3>
              <div className="space-y-2">
                {Object.entries(diagnostics.readiness_counts).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between rounded-md bg-slate-50 px-3 py-2 text-sm">
                    <span className="text-slate-600 capitalize">{humanize(key)}</span>
                    <span className="font-semibold text-slate-900">{value}</span>
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
