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

// ── Platform config ────────────────────────────────────────────────────────

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

// ── Prebuilt context chips ─────────────────────────────────────────────────

type ContextChip = {
  id: string;
  label: string;
  emoji: string;
  /** Keywords that will be injected into scraper search queries */
  keywords: string[];
  description: string;
};

export const PREBUILT_CONTEXTS: ContextChip[] = [
  {
    id: "website_app",
    label: "Website & Mobile App",
    emoji: "📱",
    keywords: ["website", "mobile app", "app crash", "login", "loading", "UI", "bug"],
    description: "Issues with the web platform or iOS/Android app",
  },
  {
    id: "listings",
    label: "Listings",
    emoji: "🏘️",
    keywords: ["listing", "property listing", "fake listing", "wrong price", "photos", "description"],
    description: "Accuracy, quality and reliability of property listings",
  },
  {
    id: "projects",
    label: "Projects & Builders",
    emoji: "🏗️",
    keywords: ["project", "builder", "construction", "delivery", "possession", "quality", "delay"],
    description: "New project launches, construction quality, possession timelines",
  },
  {
    id: "sales_agents",
    label: "Sales Process & Agents",
    emoji: "🤝",
    keywords: ["agent", "broker", "sales team", "commission", "response time", "follow up", "pushy"],
    description: "Agent behaviour, sales process, response quality",
  },
  {
    id: "post_sales",
    label: "Post-Sales Process",
    emoji: "📋",
    keywords: ["possession", "registry", "loan", "handover", "documentation", "NOC", "stamp duty"],
    description: "Registration, documentation, home loan, handover experience",
  },
  {
    id: "complaints",
    label: "Complaints & Escalations",
    emoji: "⚠️",
    keywords: ["complaint", "refund", "cheated", "fraud", "legal notice", "consumer forum", "scam"],
    description: "Fraud, refund issues, legal disputes, escalations",
  },
];

/**
 * Build the session_notes string from selected context chips + optional custom text.
 * Format: "[CONTEXT: Website & Mobile App, Listings] Custom note here"
 * If no chips selected and no custom text, returns undefined.
 */
export function buildSessionNotes(
  selectedChipIds: Set<string>,
  customText: string
): string | undefined {
  const chips = PREBUILT_CONTEXTS.filter((c) => selectedChipIds.has(c.id));
  const parts: string[] = [];

  if (chips.length > 0) {
    const chipLabels = chips.map((c) => c.label).join(", ");
    parts.push(`[CONTEXT: ${chipLabels}]`);
  }
  if (customText.trim()) {
    parts.push(customText.trim());
  }
  return parts.length > 0 ? parts.join(" ") : undefined;
}

// ── Exported helpers (used by CurrentRunPanel etc.) ────────────────────────

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

// ── Component ──────────────────────────────────────────────────────────────

export function RunSetupPanel({
  availableSources,
  runs,
  currentRunId,
  loading,
  onCreateRun,
  onSelectRun,
}: RunSetupPanelProps) {
  const [selectedSources, setSelectedSources] = useState<Set<string>>(
    () => new Set([availableSources[0] ?? "reddit"])
  );
  const [brandName, setBrandName] = useState("");
  const [selectedContexts, setSelectedContexts] = useState<Set<string>>(new Set());
  const [customContext, setCustomContext] = useState("");
  const [error, setError] = useState("");

  function toggleSource(source: string) {
    setSelectedSources((prev) => {
      const next = new Set(prev);
      if (next.has(source)) {
        if (next.size === 1) return prev; // keep at least one
        next.delete(source);
      } else {
        next.add(source);
      }
      return next;
    });
  }

  function toggleContext(id: string) {
    setSelectedContexts((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  async function handleCreateRun() {
    setError("");
    if (!brandName.trim()) { setError("Please enter a brand name"); return; }
    if (selectedSources.size === 0) { setError("Select at least one platform"); return; }

    const orderedSources = availableSources.filter((s) => selectedSources.has(s)).join(",");
    const sessionNotes = buildSessionNotes(selectedContexts, customContext);

    await onCreateRun({
      source_name: orderedSources,
      target_brand: brandName.trim(),
      status: "created",
      pipeline_stage: "created",
      trigger_mode: "manual",
      items_discovered: 0,
      items_processed: 0,
      session_notes: sessionNotes,
    });

    setBrandName("");
    setSelectedContexts(new Set());
    setCustomContext("");
    setSelectedSources(new Set([availableSources[0] ?? "reddit"]));
  }

  return (
    <SectionShell
      id="run-workspace"
      eyebrow="Step 1: Set Up"
      title="Start a New Research Session"
      description="Choose platforms, define your research focus, and start collecting feedback"
    >
      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">

        {/* ── New Session form ── */}
        <div className="card p-6 space-y-6">
          <h3 className="text-lg font-semibold text-slate-900">New Session</h3>

          {/* Platform checkboxes */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-3">
              Platforms
              <span className="ml-2 text-xs font-normal text-slate-500">select one or more</span>
            </label>
            <div className="space-y-2">
              {availableSources.map((source) => {
                const checked = selectedSources.has(source);
                return (
                  <label
                    key={source}
                    className={`flex cursor-pointer items-start gap-3 rounded-lg border px-4 py-3 transition select-none ${
                      checked ? "border-blue-300 bg-blue-50" : "border-slate-200 bg-white hover:bg-slate-50"
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
                        {PLATFORM_ICONS[source] ?? "●"} {PLATFORM_LABELS[source] ?? source}
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
                ✓ {selectedSources.size} platforms — evidence collected & analysed together
              </p>
            )}
          </div>

          {/* Brand input */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Brand to Analyze</label>
            <input
              value={brandName}
              onChange={(e) => { setBrandName(e.target.value); setError(""); }}
              placeholder="e.g. Square Yards, 99acres, NoBroker"
              className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
          </div>

          {/* Research context */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Research Context
              <span className="ml-2 text-xs font-normal text-slate-500">optional</span>
            </label>
            <p className="mb-3 text-xs text-slate-500">
              Focus the scraper on specific topics. Selected contexts guide search queries — if none selected, broad scraping runs across all signals.
            </p>

            {/* Prebuilt chips */}
            <div className="flex flex-wrap gap-2 mb-3">
              {PREBUILT_CONTEXTS.map((ctx) => {
                const active = selectedContexts.has(ctx.id);
                return (
                  <button
                    key={ctx.id}
                    type="button"
                    onClick={() => toggleContext(ctx.id)}
                    title={ctx.description}
                    className={`flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition ${
                      active
                        ? "border-violet-400 bg-violet-100 text-violet-800"
                        : "border-slate-200 bg-white text-slate-600 hover:border-violet-300 hover:bg-violet-50"
                    }`}
                  >
                    <span>{ctx.emoji}</span>
                    <span>{ctx.label}</span>
                    {active && <span className="ml-0.5 text-violet-600">✓</span>}
                  </button>
                );
              })}
            </div>

            {selectedContexts.size > 0 && (
              <p className="mb-2 text-xs text-violet-700 font-medium">
                ✓ {selectedContexts.size} focus area{selectedContexts.size > 1 ? "s" : ""} selected — scraper will prioritise these topics
              </p>
            )}

            {/* Custom context textarea */}
            <textarea
              value={customContext}
              onChange={(e) => setCustomContext(e.target.value)}
              rows={2}
              placeholder="Add custom focus (e.g. 'Focus on NRI buyer complaints about delayed possession Q2 2026')"
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

        {/* ── Recent Sessions ── */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900">Recent Sessions</h3>
            <span className="inline-block px-2.5 py-1 text-xs font-semibold bg-slate-100 text-slate-700 rounded-full">
              {runs.length}
            </span>
          </div>

          <div className="space-y-2 max-h-[520px] overflow-y-auto">
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
                // Extract context label from session_notes if present
                const contextMatch = run.session_notes?.match(/^\[CONTEXT: ([^\]]+)\]/);
                const contextLabel = contextMatch ? contextMatch[1] : null;

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
                        <p className="truncate font-medium">{run.target_brand}</p>
                        <p className="text-xs text-slate-500 mt-0.5">
                          {icons} {sourceLabel}
                          {isMulti && (
                            <span className="ml-1.5 inline-block rounded-full bg-blue-100 px-1.5 py-0.5 text-[10px] font-semibold text-blue-700">multi</span>
                          )}
                        </p>
                        {contextLabel && (
                          <p className="mt-0.5 text-xs text-violet-600 truncate">
                            🎯 {contextLabel}
                          </p>
                        )}
                        {run.session_notes && !contextLabel && (
                          <p className="mt-0.5 text-xs italic text-slate-500 truncate">
                            💬 {run.session_notes}
                          </p>
                        )}
                        <p className="text-xs text-slate-400 mt-0.5">
                          #{run.id} · {run.status}
                        </p>
                      </div>
                      {isActive && (
                        <span className="shrink-0 text-xs font-semibold text-blue-600 mt-0.5">Active</span>
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
