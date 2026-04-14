"use client";

import { useEffect, useState } from "react";
import { fetchRunInsights, type AgentInsightResponse } from "@/lib/api";

type PainPointsPanelProps = {
  runId: number | null;
};

const PRIORITY_STYLES: Record<string, string> = {
  high:   "bg-red-50 text-red-700 border-red-200",
  medium: "bg-amber-50 text-amber-700 border-amber-200",
  low:    "bg-green-50 text-green-700 border-green-200",
};

const PRIORITY_DOT: Record<string, string> = {
  high:   "bg-red-500",
  medium: "bg-amber-400",
  low:    "bg-green-500",
};

const STAGE_LABELS: Record<string, string> = {
  discovery:      "Discovery",
  consideration:  "Consideration",
  conversion:     "Conversion",
  post_discovery: "Post-Discovery",
};

const CLUSTER_LABELS: Record<string, string> = {
  inventory_quality:       "Inventory Quality",
  platform_performance:    "Platform Performance",
  lead_management:         "Lead Management",
  trust_and_safety:        "Trust & Safety",
  pricing_transparency:    "Pricing Transparency",
  search_discovery:        "Search & Discovery",
  transaction_process:     "Transaction Process",
  ux_design:               "UX Design",
  general_product_experience: "General Experience",
};

// Group insights by persona = journey_stage
function groupByPersona(insights: AgentInsightResponse[]) {
  const groups: Record<string, AgentInsightResponse[]> = {};
  for (const insight of insights) {
    const stage = insight.journey_stage ?? "unknown";
    if (!groups[stage]) groups[stage] = [];
    groups[stage].push(insight);
  }
  return groups;
}

// Deduplicate by pain_point_label, keep highest priority
function deduplicateInsights(insights: AgentInsightResponse[]): AgentInsightResponse[] {
  const seen = new Map<string, AgentInsightResponse>();
  const priorityRank: Record<string, number> = { high: 3, medium: 2, low: 1 };
  for (const insight of insights) {
    const key = insight.pain_point_label ?? insight.pain_point_summary ?? String(insight.id);
    const existing = seen.get(key);
    const rank = priorityRank[insight.priority_label ?? "low"] ?? 1;
    const existingRank = existing ? (priorityRank[existing.priority_label ?? "low"] ?? 1) : 0;
    if (!existing || rank > existingRank) seen.set(key, insight);
  }
  return Array.from(seen.values());
}

function humanizeLabel(label: string | null): string {
  if (!label) return "Unknown";
  return label.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function PainPointsPanel({ runId }: PainPointsPanelProps) {
  const [insights, setInsights] = useState<AgentInsightResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!runId) return;
    setLoading(true);
    setError("");
    fetchRunInsights(runId)
      .then(setInsights)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load insights"))
      .finally(() => setLoading(false));
  }, [runId]);

  if (!runId) {
    return (
      <section className="card p-6">
        <p className="text-[11px] font-semibold uppercase tracking-widest text-blue-600">Analysis</p>
        <h2 className="mt-1 text-lg font-semibold text-slate-900">Pain Points Summary</h2>
        <p className="mt-3 text-sm text-slate-500">Load a session and run Step 4 (Analyze) to see pain points.</p>
      </section>
    );
  }

  const deduped = deduplicateInsights(insights);
  const grouped = groupByPersona(deduped);
  const stages = Object.keys(grouped).sort();

  const highCount = deduped.filter((i) => i.priority_label === "high").length;
  const mediumCount = deduped.filter((i) => i.priority_label === "medium").length;
  const lowCount = deduped.filter((i) => i.priority_label === "low").length;

  return (
    <section id="pain-points" className="card p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-widest text-blue-600">Analysis</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-900">Pain Points Summary</h2>
          <p className="mt-0.5 text-sm text-slate-500">
            Insights for Run #{runId} — grouped by buyer journey persona
          </p>
        </div>
        {loading && <span className="text-xs text-slate-400 mt-1">Loading…</span>}
      </div>

      {error && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {!loading && insights.length === 0 && !error && (
        <div className="mt-6 rounded-lg border border-dashed border-slate-200 bg-slate-50 px-6 py-8 text-center">
          <p className="text-2xl">🔍</p>
          <p className="mt-2 text-sm font-medium text-slate-700">No pain points yet</p>
          <p className="mt-1 text-xs text-slate-500">
            Run "Step 4: Analyze" in the Run Steps panel to generate pain point insights.
          </p>
        </div>
      )}

      {deduped.length > 0 && (
        <>
          {/* Per-source summary chips */}
          {(() => {
            const sourceMap: Record<string, number> = {};
            for (const i of deduped) {
              const src = (i.source_name ?? "unknown");
              sourceMap[src] = (sourceMap[src] ?? 0) + 1;
            }
            const SOURCE_COLORS: Record<string, string> = {
              reddit:       "border-orange-200 bg-orange-50 text-orange-700",
              youtube:      "border-red-200 bg-red-50 text-red-700",
              app_reviews:  "border-purple-200 bg-purple-50 text-purple-700",
              review_sites: "border-indigo-200 bg-indigo-50 text-indigo-700",
              x:            "border-sky-200 bg-sky-50 text-sky-700",
            };
            const SOURCE_ICONS: Record<string, string> = {
              reddit: "📋", youtube: "🎬", app_reviews: "📱",
              review_sites: "⭐", x: "𝕏",
            };
            return (
              <div className="mt-4 flex flex-wrap gap-2">
                <span className="self-center text-xs font-semibold text-slate-500 uppercase tracking-wide mr-1">Sources:</span>
                {Object.entries(sourceMap).map(([src, count]) => (
                  <span
                    key={src}
                    className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold ${SOURCE_COLORS[src] ?? "border-slate-200 bg-slate-50 text-slate-700"}`}
                  >
                    <span>{SOURCE_ICONS[src] ?? "📄"}</span>
                    {humanizeLabel(src)}
                    <span className="ml-1 rounded-full bg-white/60 px-1.5 py-0.5 text-[10px] font-bold">{count}</span>
                  </span>
                ))}
              </div>
            );
          })()}

          {/* Priority summary bar */}
          <div className="mt-5 flex flex-wrap gap-3">
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2">
              <span className="h-2 w-2 rounded-full bg-red-500" />
              <span className="text-sm font-semibold text-red-700">{highCount} High</span>
            </div>
            <div className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
              <span className="h-2 w-2 rounded-full bg-amber-400" />
              <span className="text-sm font-semibold text-amber-700">{mediumCount} Medium</span>
            </div>
            <div className="flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 px-3 py-2">
              <span className="h-2 w-2 rounded-full bg-green-500" />
              <span className="text-sm font-semibold text-green-700">{lowCount} Low</span>
            </div>
            <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 ml-auto">
              <span className="text-sm font-semibold text-slate-700">{deduped.length} unique pain points across {stages.length} personas</span>
            </div>
          </div>

          {/* Persona groups */}
          <div className="mt-6 space-y-6">
            {stages.map((stage) => {
              const items = grouped[stage];
              const stageLabel = STAGE_LABELS[stage] ?? humanizeLabel(stage);
              const persona = PERSONA_DESCRIPTIONS[stage];

              return (
                <div key={stage} className="rounded-xl border border-slate-200 bg-white overflow-hidden">
                  {/* Persona header */}
                  <div className="border-b border-slate-100 bg-slate-50 px-5 py-3 flex items-center gap-3">
                    <span className="text-xl">{PERSONA_ICONS[stage] ?? "👤"}</span>
                    <div>
                      <p className="font-semibold text-slate-900 text-sm">
                        {stageLabel} Persona
                        <span className="ml-2 text-xs font-normal text-slate-500">
                          ({items.length} pain point{items.length !== 1 ? "s" : ""})
                        </span>
                      </p>
                      {persona && (
                        <p className="text-xs text-slate-500 mt-0.5">{persona}</p>
                      )}
                    </div>
                  </div>

                  {/* Pain points list */}
                  <ul className="divide-y divide-slate-100">
                    {items.map((insight, idx) => {
                      const priority = insight.priority_label ?? "medium";
                      const priorityStyle = PRIORITY_STYLES[priority] ?? PRIORITY_STYLES.medium;
                      const dotStyle = PRIORITY_DOT[priority] ?? PRIORITY_DOT.medium;
                      const cluster = CLUSTER_LABELS[insight.taxonomy_cluster ?? ""] ?? humanizeLabel(insight.taxonomy_cluster);

                      return (
                        <li key={insight.id} className="px-5 py-4">
                          <div className="flex items-start gap-3">
                            {/* Bullet number */}
                            <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-700">
                              {idx + 1}
                            </span>

                            <div className="flex-1 min-w-0">
                              <div className="flex flex-wrap items-center gap-2 mb-1">
                                <p className="font-semibold text-slate-900 text-sm">
                                  {humanizeLabel(insight.pain_point_label)}
                                </p>
                                {/* Priority badge */}
                                <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-semibold capitalize ${priorityStyle}`}>
                                  <span className={`h-1.5 w-1.5 rounded-full ${dotStyle}`} />
                                  {priority}
                                </span>
                                {/* Cluster tag */}
                                <span className="rounded-full border border-blue-200 bg-blue-50 px-2 py-0.5 text-xs text-blue-700">
                                  {cluster}
                                </span>
                              </div>

                              {/* Summary */}
                              {insight.pain_point_summary && (
                                <p className="text-sm text-slate-600 leading-relaxed">
                                  {insight.pain_point_summary}
                                </p>
                              )}

                              {/* Root cause */}
                              {insight.root_cause_hypothesis && (
                                <div className="mt-2 flex gap-2">
                                  <span className="text-xs font-semibold text-slate-400 shrink-0 mt-0.5">Root cause:</span>
                                  <span className="text-xs text-slate-500 leading-relaxed">{insight.root_cause_hypothesis}</span>
                                </div>
                              )}

                              {/* Action */}
                              {insight.action_recommendation && (
                                <div className="mt-1 flex gap-2">
                                  <span className="text-xs font-semibold text-slate-400 shrink-0 mt-0.5">Action:</span>
                                  <span className="text-xs text-slate-500 leading-relaxed">{insight.action_recommendation}</span>
                                </div>
                              )}
                            </div>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              );
            })}
          </div>
        </>
      )}
    </section>
  );
}

const PERSONA_ICONS: Record<string, string> = {
  discovery:      "🔍",
  consideration:  "🤝",
  conversion:     "💳",
  post_discovery: "📋",
  unknown:        "👤",
};

const PERSONA_DESCRIPTIONS: Record<string, string> = {
  discovery:      "User is browsing listings, filtering, or researching properties.",
  consideration:  "User is contacting agents, requesting callbacks, or evaluating options.",
  conversion:     "User is booking visits, making payments, or applying for loans.",
  post_discovery: "User has explored options and is comparing or following up.",
};
