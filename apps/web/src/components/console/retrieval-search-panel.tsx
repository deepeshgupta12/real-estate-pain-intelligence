"use client";

import { useRef, useState } from "react";
import { searchRetrieval, type RetrievalSearchResult } from "@/lib/api";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function scoreBar(score: number): string {
  // score is typically 0-1 cosine similarity; clamp and render as Tailwind width
  const pct = Math.min(100, Math.max(0, Math.round(score * 100)));
  return `${pct}%`;
}

function scoreColor(score: number): string {
  if (score >= 0.8) return "bg-green-500";
  if (score >= 0.55) return "bg-amber-400";
  return "bg-slate-300";
}

function docTypeBadge(docType: string): string {
  switch (docType) {
    case "pain_point":
      return "bg-red-50 text-red-700 border-red-200";
    case "evidence":
      return "bg-blue-50 text-blue-700 border-blue-200";
    case "insight":
      return "bg-purple-50 text-purple-700 border-purple-200";
    default:
      return "bg-slate-50 text-slate-600 border-slate-200";
  }
}

function truncate(text: string | null, maxLen = 320): string {
  if (!text) return "—";
  return text.length > maxLen ? text.slice(0, maxLen) + "…" : text;
}

// ---------------------------------------------------------------------------
// Suggestion chips
// ---------------------------------------------------------------------------

const SAMPLE_QUERIES = [
  "hidden charges in booking",
  "agent not responding",
  "stale listings already sold",
  "app crash filter reset",
  "fraud builder verification",
  "slow app load time",
  "price mismatch listing",
];

// ---------------------------------------------------------------------------
// Result card
// ---------------------------------------------------------------------------

function ResultCard({
  result,
  rank,
}: {
  result: RetrievalSearchResult;
  rank: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const text = result.document_text ?? "";

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      {/* Rank + score */}
      <div className="mb-2 flex items-center gap-3">
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 text-[11px] font-bold text-white">
          {rank}
        </span>
        <div className="flex flex-1 items-center gap-2">
          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
            <div
              className={`h-full rounded-full transition-all ${scoreColor(result.score)}`}
              style={{ width: scoreBar(result.score) }}
            />
          </div>
          <span className="w-12 text-right text-xs font-semibold text-slate-500">
            {(result.score * 100).toFixed(0)}%
          </span>
        </div>

        {/* Type badge */}
        <span
          className={`rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${docTypeBadge(result.document_type)}`}
        >
          {result.document_type.replace(/_/g, " ")}
        </span>
      </div>

      {/* Title */}
      {result.title && (
        <p className="mb-1 text-sm font-semibold text-slate-800">{result.title}</p>
      )}

      {/* Document text */}
      <p className="text-sm leading-relaxed text-slate-600">
        {expanded ? text : truncate(text)}
      </p>

      {/* Footer */}
      <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-slate-400">
        {text.length > 320 && (
          <button
            type="button"
            onClick={() => setExpanded((e) => !e)}
            className="font-medium text-blue-600 hover:underline"
          >
            {expanded ? "Show less" : "Show more"}
          </button>
        )}
        {result.raw_evidence_id && (
          <span>Evidence #{result.raw_evidence_id}</span>
        )}
        {result.agent_insight_id && (
          <span>Insight #{result.agent_insight_id}</span>
        )}
        {result.language_code && (
          <span className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[10px]">
            {result.language_code}
          </span>
        )}
        <span className="ml-auto font-mono text-[10px]">
          doc #{result.retrieval_document_id}
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

export function RetrievalSearchPanel({ runId }: Props) {
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [results, setResults] = useState<RetrievalSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleSearch(overrideQuery?: string) {
    const q = (overrideQuery ?? query).trim();
    if (!q) return;

    setLoading(true);
    setError("");
    setResults([]);

    try {
      const data = await searchRetrieval({
        query: q,
        topK,
        runId: runId ?? undefined,
      });
      setResults(data);
      setSearched(true);
      if (overrideQuery) setQuery(overrideQuery);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed.");
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") handleSearch();
  }

  return (
    <section id="retrieval-search" className="card p-5">
      {/* Header */}
      <div className="mb-5">
        <p className="text-[11px] font-semibold uppercase tracking-widest text-blue-600">
          Retrieval Search
        </p>
        <h2 className="mt-0.5 text-lg font-semibold tracking-tight text-slate-900">
          Semantic Evidence Search
        </h2>
        <p className="mt-0.5 text-sm text-slate-500">
          Search through collected and indexed evidence using natural language.
          {runId ? ` Scoped to run #${runId}.` : " Searching across all runs."}
        </p>
      </div>

      {/* Search bar */}
      <div className="flex gap-2">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="e.g. hidden charges, agent not responding, app crash…"
          className="flex-1 rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-800 shadow-sm placeholder:text-slate-400 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-300"
        />
        <select
          value={topK}
          onChange={(e) => setTopK(Number(e.target.value))}
          className="rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-600 shadow-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-300"
          title="Number of results"
        >
          <option value={3}>Top 3</option>
          <option value={5}>Top 5</option>
          <option value={10}>Top 10</option>
          <option value={20}>Top 20</option>
        </select>
        <button
          type="button"
          onClick={() => handleSearch()}
          disabled={loading || !query.trim()}
          className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </div>

      {/* Sample query chips */}
      <div className="mt-3 flex flex-wrap gap-1.5">
        <span className="text-xs text-slate-400">Try:</span>
        {SAMPLE_QUERIES.map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => handleSearch(q)}
            disabled={loading}
            className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-0.5 text-xs font-medium text-slate-600 transition hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700 disabled:opacity-50"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
          {error.includes("No documents") || error.includes("not found") ? (
            <p className="mt-1 text-xs text-red-500">
              Make sure you have run the "Build Search Library" step first to index evidence.
            </p>
          ) : null}
        </div>
      )}

      {/* Results */}
      {loading ? (
        <div className="mt-4 space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 animate-pulse rounded-lg bg-slate-100" />
          ))}
        </div>
      ) : results.length > 0 ? (
        <div className="mt-4 space-y-3">
          <p className="text-xs text-slate-400">
            Found {results.length} result{results.length !== 1 ? "s" : ""} for &ldquo;{query}&rdquo;
          </p>
          {results.map((result, idx) => (
            <ResultCard key={result.retrieval_document_id} result={result} rank={idx + 1} />
          ))}
        </div>
      ) : searched && !loading ? (
        <div className="mt-6 flex flex-col items-center rounded-xl border border-dashed border-slate-200 py-12 text-center">
          <div className="text-3xl">🔎</div>
          <p className="mt-2 font-medium text-slate-600">No results found</p>
          <p className="mt-1 text-sm text-slate-400">
            Try a different search term, or make sure the "Build Search Library" step has been run.
          </p>
        </div>
      ) : !searched ? (
        <div className="mt-6 flex flex-col items-center rounded-xl border border-dashed border-slate-100 py-10 text-center">
          <div className="text-3xl">💡</div>
          <p className="mt-2 text-sm font-medium text-slate-500">
            Enter a search query above to explore the indexed evidence
          </p>
          <p className="mt-1 text-xs text-slate-400">
            The search uses semantic similarity — try plain English descriptions of pain points.
          </p>
        </div>
      ) : null}
    </section>
  );
}
