"use client";

import { useState } from "react";
import { ScrapeRunCreatePayload, ScrapeRunResponse } from "@/lib/api";
import { SectionShell } from "@/components/console/section-shell";

type RunSetupPanelProps = {
  availableSources: string[];
  runs: ScrapeRunResponse[];
  currentRunId: number | null;
  loading: boolean;
  onCreateRun: (payload: ScrapeRunCreatePayload) => Promise<void>;
  onSelectRun: (runId: number) => Promise<void>;
};

function humanize(value: string): string {
  return value.replaceAll("_", " ");
}

const PLATFORM_ICONS: Record<string, string> = {
  reddit: "🔴",
  youtube: "▶️",
  "app_reviews": "⭐",
  "review_sites": "🌐",
};

export function RunSetupPanel({
  availableSources,
  runs,
  currentRunId,
  loading,
  onCreateRun,
  onSelectRun,
}: RunSetupPanelProps) {
  const [sourceName, setSourceName] = useState(availableSources[0] ?? "reddit");
  const [brandName, setBrandName] = useState("");
  const [startType] = useState("manual");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");

  async function handleCreateRun() {
    setError("");
    if (!brandName.trim()) {
      setError("Please enter a brand name");
      return;
    }

    await onCreateRun({
      source_name: sourceName,
      target_brand: brandName.trim(),
      status: "created",
      pipeline_stage: "created",
      trigger_mode: startType,
      items_discovered: 0,
      items_processed: 0,
      orchestrator_notes: notes.trim() || undefined,
    });

    setBrandName("");
    setNotes("");
  }

  return (
    <SectionShell
      id="run-workspace"
      eyebrow="Step 1: Set Up"
      title="Start a New Research Session"
      description="Choose a platform and brand to analyze customer feedback from"
    >
      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-slate-900">New Session</h3>

          <div className="mt-5 space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Platform
              </label>
              <select
                value={sourceName}
                onChange={(e) => setSourceName(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {availableSources.map((source) => (
                  <option key={source} value={source}>
                    {PLATFORM_ICONS[source] || "●"} {humanize(source)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Brand to Analyze
              </label>
              <input
                value={brandName}
                onChange={(e) => {
                  setBrandName(e.target.value);
                  setError("");
                }}
                placeholder="e.g. Square Yards, 99acres"
                className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Notes (optional)
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                placeholder="Add context for this research session"
                className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <button
              type="button"
              onClick={handleCreateRun}
              disabled={loading || !brandName.trim()}
              className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Starting..." : "Start Research →"}
            </button>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900">Recent Sessions</h3>
            <span className="inline-block px-2.5 py-1 text-xs font-semibold bg-slate-100 text-slate-700 rounded-full">
              {runs.length}
            </span>
          </div>

          <div className="space-y-2 max-h-80 overflow-y-auto">
            {runs.length === 0 ? (
              <div className="rounded-lg bg-slate-50 px-4 py-8 text-center text-sm text-slate-600">
                No sessions yet. Create one to get started.
              </div>
            ) : (
              runs.slice(0, 8).map((run) => {
                const isActive = currentRunId === run.id;
                const platformIcon = PLATFORM_ICONS[run.source_name] || "●";

                return (
                  <button
                    key={run.id}
                    type="button"
                    onClick={() => onSelectRun(run.id)}
                    disabled={loading}
                    className={`w-full rounded-lg border px-4 py-3 text-left transition text-sm ${
                      isActive
                        ? "border-blue-300 bg-blue-50 font-semibold text-slate-900"
                        : "border-slate-200 bg-white hover:bg-slate-50 text-slate-700"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-medium">
                          {platformIcon} {run.target_brand}
                        </p>
                        <p className="text-xs text-slate-500">
                          #{run.id} • {humanize(run.status)}
                        </p>
                      </div>
                      {isActive && (
                        <span className="shrink-0 text-xs font-semibold text-blue-600">
                          Active
                        </span>
                      )}
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>
      </div>
    </SectionShell>
  );
}