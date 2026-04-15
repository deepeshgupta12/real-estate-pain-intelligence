"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchEvidenceItems, type RawEvidenceResponse } from "@/lib/api";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const SOURCE_LABELS: Record<string, string> = {
  reddit: "Reddit",
  youtube: "YouTube",
  review_sites: "App Reviews",
  app_reviews: "App Reviews",
  x: "X / Social",
  twitter: "X / Social",
};

const CONTENT_TYPE_COLORS: Record<string, string> = {
  post: "bg-blue-50 text-blue-700 border-blue-200",
  comment: "bg-indigo-50 text-indigo-700 border-indigo-200",
  review: "bg-purple-50 text-purple-700 border-purple-200",
  video: "bg-red-50 text-red-700 border-red-200",
};

const ALL_SOURCES = ["reddit", "youtube", "review_sites", "app_reviews", "x"];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function truncate(text: string, maxLen = 280): string {
  return text.length > maxLen ? text.slice(0, maxLen) + "…" : text;
}

function relativeTime(isoStr: string | null): string {
  if (!isoStr) return "—";
  const diff = Date.now() - new Date(isoStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 2) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function sourceLabel(name: string): string {
  return SOURCE_LABELS[name] ?? name;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function EvidenceCard({ item }: { item: RawEvidenceResponse }) {
  const [expanded, setExpanded] = useState(false);
  const text = item.cleaned_text ?? item.raw_text ?? "";
  const ctColor =
    CONTENT_TYPE_COLORS[item.content_type] ?? "bg-slate-50 text-slate-600 border-slate-200";

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm transition hover:shadow-md">
      {/* Header row */}
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="font-semibold text-slate-700">{sourceLabel(item.source_name)}</span>
        <span className="text-slate-300">·</span>
        <span className={`rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${ctColor}`}>
          {item.content_type}
        </span>
        {item.platform_name && (
          <>
            <span className="text-slate-300">·</span>
            <span className="text-slate-500">{item.platform_name}</span>
          </>
        )}
        {item.author_name && (
          <>
            <span className="text-slate-300">·</span>
            <span className="text-slate-400">@{item.author_name}</span>
          </>
        )}
        <span className="ml-auto text-slate-400">{relativeTime(item.fetched_at)}</span>
      </div>

      {/* Text */}
      <p className="mt-2 text-sm leading-relaxed text-slate-700">
        {expanded ? text : truncate(text)}
      </p>

      {/* Expand / Source link row */}
      <div className="mt-2 flex flex-wrap items-center gap-3 text-xs">
        {text.length > 280 && (
          <button
            type="button"
            onClick={() => setExpanded((e) => !e)}
            className="font-medium text-blue-600 hover:underline"
          >
            {expanded ? "Show less" : "Show more"}
          </button>
        )}
        {item.source_url && (
          <a
            href={item.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-slate-400 hover:text-blue-600 hover:underline"
          >
            View source ↗
          </a>
        )}
        <span className="ml-auto rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[10px] text-slate-400">
          #{item.id}
        </span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main panel
// ---------------------------------------------------------------------------

type Props = {
  runId: number | null;
};

export function EvidenceExplorerPanel({ runId }: Props) {
  const [items, setItems] = useState<RawEvidenceResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedSource, setSelectedSource] = useState<string>("all");
  const [selectedType, setSelectedType] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchEvidenceItems({
        runId: runId ?? undefined,
        limit: 200,
      });
      setItems(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load evidence.");
    } finally {
      setLoading(false);
    }
  }, [runId]);

  useEffect(() => {
    load();
  }, [load]);

  // Derived: unique sources from loaded items
  const availableSources = Array.from(new Set(items.map((i) => i.source_name)));
  const availableTypes = Array.from(new Set(items.map((i) => i.content_type)));

  const filtered = items.filter((item) => {
    if (selectedSource !== "all" && item.source_name !== selectedSource) return false;
    if (selectedType !== "all" && item.content_type !== selectedType) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const text = (item.cleaned_text ?? item.raw_text ?? "").toLowerCase();
      const author = (item.author_name ?? "").toLowerCase();
      if (!text.includes(q) && !author.includes(q)) return false;
    }
    return true;
  });

  // Summary counts
  const bySource: Record<string, number> = {};
  for (const item of items) {
    bySource[item.source_name] = (bySource[item.source_name] ?? 0) + 1;
  }

  return (
    <section id="evidence-explorer" className="card p-5">
      {/* Section header */}
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-widest text-blue-600">
            Evidence Explorer
          </p>
          <h2 className="mt-0.5 text-lg font-semibold tracking-tight text-slate-900">
            Raw Collected Evidence
          </h2>
          <p className="mt-0.5 text-sm text-slate-500">
            Browse every post, review, and comment collected for this session.
            {runId ? ` Showing run #${runId}.` : " Showing all runs."}
          </p>
        </div>

        <button
          type="button"
          onClick={load}
          disabled={loading}
          className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 shadow-sm hover:bg-slate-50 disabled:opacity-50"
        >
          {loading ? "Loading…" : "↻ Refresh"}
        </button>
      </div>

      {/* Source summary chips */}
      {items.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {Object.entries(bySource).map(([src, count]) => (
            <span
              key={src}
              className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-600"
            >
              <span className="font-semibold">{sourceLabel(src)}</span>
              <span className="rounded-full bg-slate-200 px-1.5 py-0.5 text-[10px] font-bold text-slate-700">
                {count}
              </span>
            </span>
          ))}
          <span className="inline-flex items-center gap-1.5 rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
            Total: {items.length}
          </span>
        </div>
      )}

      {/* Filters */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search text or author…"
          className="min-w-[200px] flex-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 shadow-sm placeholder:text-slate-400 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-300"
        />

        <select
          value={selectedSource}
          onChange={(e) => setSelectedSource(e.target.value)}
          className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-sm text-slate-600 shadow-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-300"
        >
          <option value="all">All sources</option>
          {availableSources.map((s) => (
            <option key={s} value={s}>
              {sourceLabel(s)}
            </option>
          ))}
        </select>

        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-sm text-slate-600 shadow-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-300"
        >
          <option value="all">All types</option>
          {availableTypes.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>

        {(selectedSource !== "all" || selectedType !== "all" || searchQuery) && (
          <button
            type="button"
            onClick={() => {
              setSelectedSource("all");
              setSelectedType("all");
              setSearchQuery("");
            }}
            className="text-xs font-medium text-slate-400 hover:text-slate-600"
          >
            ✕ Clear filters
          </button>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Content */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 animate-pulse rounded-lg bg-slate-100" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 py-16 text-center">
          <div className="text-3xl">🔍</div>
          <p className="mt-2 font-medium text-slate-600">
            {items.length === 0 ? "No evidence collected yet" : "No results match your filters"}
          </p>
          <p className="mt-1 text-sm text-slate-400">
            {items.length === 0
              ? 'Run "Collect Feedback" to gather data from sources.'
              : "Try adjusting the source, type, or search term."}
          </p>
        </div>
      ) : (
        <>
          <p className="mb-3 text-xs text-slate-400">
            Showing {filtered.length} of {items.length} items
          </p>
          <div className="space-y-3">
            {filtered.map((item) => (
              <EvidenceCard key={item.id} item={item} />
            ))}
          </div>
        </>
      )}
    </section>
  );
}
