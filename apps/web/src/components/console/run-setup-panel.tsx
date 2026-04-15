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

const PLATFORM_ICONS: Record<string, string> = {
  reddit: "🔴",
  youtube: "▶️",
  app_reviews: "⭐",
  review_sites: "🌐",
  x: "𝕏",
};

const PLATFORM_LABELS: Record<string, string> = {
  reddit: "Reddit",
  youtube: "YouTube",
  app_reviews: "App Reviews",
  review_sites: "Review Sites",
  x: "X (Twitter)",
};

const PLATFORM_DESCRIPTIONS: Record<string, string> = {
  reddit: "Posts & comments from relevant subreddits",
  youtube: "Video titles & descriptions mentioning the brand",
  app_reviews: "Google Play + Apple App Store reviews",
  review_sites: "Third-party review portals & listing sites",
  x: "Tweets mentioning the brand",
};

/** Parse a stored comma-separated source_name into a display string of icons. */
export function formatSourceIcons(sourceName: string): string {
  return sourceName
    .split(",")
    .map((s) => PLATFORM_ICONS[s.trim()] ?? "●")
    .join(" ");
}

/** Parse a stored comma-separated source_name into a human-readable label. */
export function formatSourceLabel(sourceName: string): string {
  const parts = sourceName.split(",").map((s) => PLATFORM_LABELS[s.trim()] ?? s.trim());
  if (parts.length === 1) return parts[0];
  if (parts.length === 2) return parts.join(" + ");
  return `${parts.slice(0, -1).join(", ")} + ${parts[parts.length - 1]}`;
}

export function RunSetupPanel({
  availableSources,
  runs,
  currentRunId,
  loading,
  onCreateRun,
  onSelectRun,
}: RunSetupPanelProps) {
  // Multi-select: set of chosen source names
  const [selectedSources, setSelectedSources] = useState<Set<string>>(
    () => new Set([availableSources[0] ?? "reddit"])
  );
  const [brandName, setBrandName] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");

  function toggleSource(source: string) {
    setSelectedSources((prev) => {
      const next = new Set(prev);
      if (next.has(source)) {
        // Prevent deselecting the last platform
        if (next.size === 1) return prev;
        next.delete(source);
      } else {
        next.add(source);
      }
      return next;
    });
  }

  async function handleCreateRun() {
    setError("");
    if (!brandName.trim()) {
      setError("Please enter a brand name");
      return;
    }
    if (selectedSources.size === 0) {
      setError("Select at least one platform");
      return;
    }

    // Preserve the order from availableSources for a consistent DB value
    const orderedSources = availableSources
      .filter((s) => selectedSources.has(s))
      .join(",");

    await onCreateRun({
      source_name: orderedSources,
      target_brand: brandName.trim(),
      status: "created",
      pipeline_stage: "created",
      trigger_mode: "manual",
      items_discovered: 0,
      items_processed: 0,
      session_notes: notes.trim() || undefined,
    });

    setBrandName("");
    setNotes("");
    setSelectedSources(new Set([availableSources[0] ?? "reddit"]));
  }

  return (
    <SectionShell
      id="run-workspace"
      eyebrow="Step 1: Set Up"
      title="Start a New Research Session"
      description="Choose one or more platforms and a brand to analyze customer feedback from"
    >
      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        {/* ── New Session form ── */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-slate-900">New Session</h3>

          <div className="mt-5 space-y-5">
            {/* Platform checkboxes */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-3">
                Platforms
                <span className="ml-2 text-xs font-normal text-slate-500">
                  select one or more
                </span>
              </label>
              <div className="space-y-2">
                {availableSources.map((source) => {
                  const checked = selectedSources.has(source);
                  return (
                    <label
                      key={source}
                      className={`flex cursor-pointer items-start gap-3 rounded-lg border px-4 py-3 transition select-none ${
                        checked
                          ? "border-blue-300 bg-blue-50"
                          : "border-slate-200 bg-white hover:bg-slate-50"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleSource(source)}
                        className="mt-0.5 h-4 w-4 shrink-0 rounded border-slate-300 accent-blue-600"
                      />
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-slate-900">
                          {PLATFORM_ICONS[source] ?? "●"}{" "}
                          {PLATFORM_LABELS[source] ?? source}
                        </p>
                        <p className="text-xs text-slate-500 mt-0.5">
                          {PLATFORM_DESCRIPTIONS[source] ?? ""}
                        </p>
                      </div>
                    </label>
                  );
                })}
              </div>
              {selectedSources.size > 1 && (
                <p className="mt-2 text-xs text-blue-600 font-medium">
                  ✓ {selectedSources.size} platforms selected — evidence will be collected and analysed together
                </p>
              )}
            </div>

            {/* Brand input */}
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

            {/* Session notes */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Session Notes
                <span className="ml-2 text-xs font-normal text-slate-500">optional</span>
              </label>
              <p className="mb-2 text-xs text-slate-500">
                Context that persists with this session (e.g. "Focus on checkout complaints Q2 2026"). Visible in session details and can guide AI analysis.
              </p>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                placeholder="Add research context, focus areas, or hypotheses…"
                className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <button
              type="button"
              onClick={handleCreateRun}
              disabled={loading || !brandName.trim() || selectedSources.size === 0}
              className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Starting..." : "Start Research →"}
            </button>
          </div>
        </div>

        {/* ── Recent Sessions ── */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900">Recent Sessions</h3>
            <span className="inline-block px-2.5 py-1 text-xs font-semibold bg-slate-100 text-slate-700 rounded-full">
              {runs.length}
            </span>
          </div>

          <div className="space-y-2 max-h-[480px] overflow-y-auto">
            {runs.length === 0 ? (
              <div className="rounded-lg bg-slate-50 px-4 py-8 text-center text-sm text-slate-600">
                No sessions yet. Create one to get started.
              </div>
            ) : (
              runs.slice(0, 10).map((run) => {
                const isActive = currentRunId === run.id;
                const icons = formatSourceIcons(run.source_name);
                const sourceLabel = formatSourceLabel(run.source_name);
                const isMulti = run.source_name.includes(",");

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
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-medium">
                          {run.target_brand}
                        </p>
                        <p className="text-xs text-slate-500 mt-0.5">
                          {icons} {sourceLabel}
                        </p>
                        <p className="text-xs text-slate-400 mt-0.5">
                          #{run.id} · {run.status}
                          {isMulti && (
                            <span className="ml-1.5 inline-block rounded-full bg-blue-100 px-1.5 py-0.5 text-[10px] font-semibold text-blue-700">
                              multi
                            </span>
                          )}
                        </p>
                        {run.session_notes && (
                          <p className="mt-1 text-xs italic text-slate-500 truncate">
                            💬 {run.session_notes}
                          </p>
                        )}
                      </div>
                      {isActive && (
                        <span className="shrink-0 text-xs font-semibold text-blue-600 mt-0.5">
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
