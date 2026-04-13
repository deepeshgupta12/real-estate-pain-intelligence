"use client";

import { useEffect, useMemo, useState } from "react";
import {
  approveReviewItem,
  bulkApproveReviewItems,
  bulkRejectReviewItems,
  fetchReviewDetail,
  fetchReviewQueue,
  fetchReviewSummary,
  rejectReviewItem,
  ReviewQueueItem,
  ReviewSummaryResponse,
} from "@/lib/api";
import { SectionShell } from "@/components/console/section-shell";

type ReviewConsolePanelProps = {
  initialRunId: number | null;
  activeRunId: number | null;
  initialSummary: ReviewSummaryResponse;
  initialQueue: ReviewQueueItem[];
};

function getAnalysisMode(item: ReviewQueueItem): string {
  const snapshotMode = item.insight_snapshot?.analysis_mode;
  if (typeof snapshotMode === "string" && snapshotMode.trim()) {
    return snapshotMode;
  }

  const metadataMode = item.metadata_json?.analysis_mode;
  if (typeof metadataMode === "string" && metadataMode.trim()) {
    return metadataMode;
  }

  return "N/A";
}

function getFetchMode(item: ReviewQueueItem): string {
  const evidenceMode = item.evidence_snapshot?.metadata_json?.fetch_mode;
  if (typeof evidenceMode === "string" && evidenceMode.trim()) {
    return evidenceMode;
  }

  const metadataMode = item.metadata_json?.fetch_mode;
  if (typeof metadataMode === "string" && metadataMode.trim()) {
    return metadataMode;
  }

  return "unknown";
}

function getSourceName(item: ReviewQueueItem): string {
  return (
    item.evidence_snapshot?.source_name ||
    (typeof item.metadata_json?.source_name === "string"
      ? item.metadata_json.source_name
      : "") ||
    "N/A"
  );
}

export function ReviewConsolePanel({
  initialRunId,
  activeRunId,
  initialSummary,
  initialQueue,
}: ReviewConsolePanelProps) {
  const [summary, setSummary] = useState<ReviewSummaryResponse>(initialSummary);
  const [queue, setQueue] = useState<ReviewQueueItem[]>(initialQueue);
  const [selectedItem, setSelectedItem] = useState<ReviewQueueItem | null>(
    initialQueue[0] ?? null,
  );
  const [runId, setRunId] = useState(initialRunId ? String(initialRunId) : "");
  const [reviewStatus, setReviewStatus] = useState("");
  const [reviewerDecision, setReviewerDecision] = useState("");
  const [priorityLabel, setPriorityLabel] = useState("");
  const [analysisMode, setAnalysisMode] = useState("");
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [reviewerNotes, setReviewerNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");

  const selectedIdSet = useMemo(() => new Set(selectedIds), [selectedIds]);

  const liveCount = queue.filter((item) => getFetchMode(item) === "live").length;
  const stubCount = queue.filter((item) => getFetchMode(item) === "stub").length;
  const unknownFetchCount = queue.filter(
    (item) => !["live", "stub"].includes(getFetchMode(item)),
  ).length;

  const llmUsedCount = queue.filter(
    (item) => item.insight_snapshot?.llm_used === true,
  ).length;

  async function reloadData(overrideRunId?: string) {
    const effectiveRunId = overrideRunId ?? runId;
    const parsedRunId = effectiveRunId ? Number(effectiveRunId) : undefined;

    const [summaryData, queueData] = await Promise.all([
      fetchReviewSummary(parsedRunId),
      fetchReviewQueue({
        runId: parsedRunId,
        reviewStatus: reviewStatus || undefined,
        reviewerDecision: reviewerDecision || undefined,
        priorityLabel: priorityLabel || undefined,
        analysisMode: analysisMode || undefined,
        includeDetails: true,
        limit: 20,
        offset: 0,
      }),
    ]);

    setSummary(summaryData);
    setQueue(queueData);

    if (selectedItem) {
      const found = queueData.find((item) => item.id === selectedItem.id);
      setSelectedItem(found ?? queueData[0] ?? null);
    } else {
      setSelectedItem(queueData[0] ?? null);
    }
  }

  useEffect(() => {
    const nextRunValue = activeRunId ? String(activeRunId) : "";

    setRunId(nextRunValue);
    setSelectedIds([]);
    setReviewerNotes("");
    setError("");
    setStatusMessage("");

    if (activeRunId === initialRunId) {
      setSummary(initialSummary);
      setQueue(initialQueue);
      setSelectedItem(initialQueue[0] ?? null);
      return;
    }

    let cancelled = false;

    async function syncToActiveRun() {
      setLoading(true);

      try {
        const parsedRunId = nextRunValue ? Number(nextRunValue) : undefined;
        const [summaryData, queueData] = await Promise.all([
          fetchReviewSummary(parsedRunId),
          fetchReviewQueue({
            runId: parsedRunId,
            includeDetails: true,
            limit: 20,
            offset: 0,
          }),
        ]);

        if (cancelled) {
          return;
        }

        setSummary(summaryData);
        setQueue(queueData);
        setSelectedItem(queueData[0] ?? null);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Failed to sync review console to the active run",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void syncToActiveRun();

    return () => {
      cancelled = true;
    };
  }, [activeRunId, initialQueue, initialRunId, initialSummary]);

  async function handleLoadQueue() {
    setLoading(true);
    setError("");
    setStatusMessage("");

    try {
      await reloadData();
      setSelectedIds([]);
      setStatusMessage(
        runId
          ? `Loaded review queue for run #${runId}.`
          : "Loaded review queue across all runs.",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load review queue");
    } finally {
      setLoading(false);
    }
  }

  async function handleSelectDetail(id: number) {
    setError("");
    setStatusMessage("");

    try {
      const detail = await fetchReviewDetail(id);
      setSelectedItem(detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load review detail");
    }
  }

  async function handleSingleAction(action: "approve" | "reject", id: number) {
    setActionLoading(true);
    setError("");
    setStatusMessage("");

    try {
      if (action === "approve") {
        await approveReviewItem(id, { reviewer_notes: reviewerNotes || undefined });
      } else {
        await rejectReviewItem(id, { reviewer_notes: reviewerNotes || undefined });
      }

      await reloadData();
      const detail = await fetchReviewDetail(id);
      setSelectedItem(detail);
      setStatusMessage(
        action === "approve"
          ? "Review item approved successfully."
          : "Review item rejected successfully.",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Review action failed");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleBulkAction(action: "approve" | "reject") {
    if (selectedIds.length === 0) {
      setError("Select at least one review item for a bulk action.");
      return;
    }

    setActionLoading(true);
    setError("");
    setStatusMessage("");

    try {
      if (action === "approve") {
        await bulkApproveReviewItems({
          item_ids: selectedIds,
          reviewer_notes: reviewerNotes || undefined,
        });
      } else {
        await bulkRejectReviewItems({
          item_ids: selectedIds,
          reviewer_notes: reviewerNotes || undefined,
        });
      }

      await reloadData();
      setSelectedIds([]);
      setStatusMessage(
        action === "approve"
          ? "Bulk approve completed successfully."
          : "Bulk reject completed successfully.",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bulk review action failed");
    } finally {
      setActionLoading(false);
    }
  }

  function toggleSelection(id: number) {
    setSelectedIds((current) =>
      current.includes(id)
        ? current.filter((itemId) => itemId !== id)
        : [...current, id],
    );
  }

  function handleUseActiveRun() {
    setRunId(activeRunId ? String(activeRunId) : "");
    setStatusMessage("");
    setError("");
  }

  function handleShowAllRuns() {
    setRunId("");
    setStatusMessage("");
    setError("");
  }

  return (
    <SectionShell
      id="review-console"
      eyebrow="Human validation"
      title="Review console"
      description="Review summary, filtered queue, joined detail, and single or bulk moderation actions for agent-generated insights."
    >
      <div className="grid gap-4 md:grid-cols-4 xl:grid-cols-7">
        <div className="rounded-2xl border border-white/10 bg-black/10 p-4">
          <p className="text-xs uppercase tracking-[0.16em] text-white/45">Total</p>
          <p className="mt-2 text-2xl font-semibold text-white">{summary.total_items}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-black/10 p-4">
          <p className="text-xs uppercase tracking-[0.16em] text-white/45">Pending</p>
          <p className="mt-2 text-2xl font-semibold text-amber-300">
            {summary.pending_review_count}
          </p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-black/10 p-4">
          <p className="text-xs uppercase tracking-[0.16em] text-white/45">Approved</p>
          <p className="mt-2 text-2xl font-semibold text-emerald-300">
            {summary.approved_count}
          </p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-black/10 p-4">
          <p className="text-xs uppercase tracking-[0.16em] text-white/45">Rejected</p>
          <p className="mt-2 text-2xl font-semibold text-rose-300">
            {summary.rejected_count}
          </p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-black/10 p-4">
          <p className="text-xs uppercase tracking-[0.16em] text-white/45">LLM assisted</p>
          <p className="mt-2 text-2xl font-semibold text-cyan-200">
            {summary.llm_assisted_count}
          </p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-black/10 p-4">
          <p className="text-xs uppercase tracking-[0.16em] text-white/45">Live-backed</p>
          <p className="mt-2 text-2xl font-semibold text-emerald-300">{liveCount}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-black/10 p-4">
          <p className="text-xs uppercase tracking-[0.16em] text-white/45">Stub-backed</p>
          <p className="mt-2 text-2xl font-semibold text-amber-300">{stubCount}</p>
        </div>
      </div>

      <div className="mt-5 rounded-3xl border border-white/10 bg-black/10 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handleUseActiveRun}
            className="rounded-2xl border border-cyan-400/30 bg-cyan-400/10 px-4 py-2 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-400/15"
          >
            Use active run{activeRunId ? ` #${activeRunId}` : ""}
          </button>

          <button
            type="button"
            onClick={handleShowAllRuns}
            className="rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white/10"
          >
            Show all runs
          </button>

          <span className="text-sm text-white/60">
            Current scope: {runId ? `run #${runId}` : "all runs"}
          </span>

          <span className="text-sm text-white/45">
            Unknown fetch mode items: {unknownFetchCount}
          </span>

          <span className="text-sm text-white/45">
            Queue items using LLM: {llmUsedCount}
          </span>
        </div>
      </div>

      <div className="mt-5 grid gap-3 rounded-3xl border border-white/10 bg-black/10 p-4 md:grid-cols-2 xl:grid-cols-6">
        <input
          value={runId}
          onChange={(e) => setRunId(e.target.value)}
          placeholder="Run id"
          className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none placeholder:text-white/35"
        />
        <select
          value={reviewStatus}
          onChange={(e) => setReviewStatus(e.target.value)}
          className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none"
        >
          <option value="">All review status</option>
          <option value="pending_review">pending_review</option>
          <option value="reviewed">reviewed</option>
        </select>
        <select
          value={reviewerDecision}
          onChange={(e) => setReviewerDecision(e.target.value)}
          className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none"
        >
          <option value="">All decisions</option>
          <option value="approved">approved</option>
          <option value="rejected">rejected</option>
        </select>
        <select
          value={priorityLabel}
          onChange={(e) => setPriorityLabel(e.target.value)}
          className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none"
        >
          <option value="">All priority</option>
          <option value="high">high</option>
          <option value="medium">medium</option>
          <option value="low">low</option>
        </select>
        <select
          value={analysisMode}
          onChange={(e) => setAnalysisMode(e.target.value)}
          className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none"
        >
          <option value="">All analysis modes</option>
          <option value="llm_assisted">llm_assisted</option>
          <option value="deterministic_only">deterministic_only</option>
          <option value="deterministic_fallback">deterministic_fallback</option>
        </select>
        <button
          onClick={handleLoadQueue}
          disabled={loading}
          className="rounded-2xl border border-cyan-400/30 bg-cyan-400/10 px-5 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-400/15 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Loading..." : "Load queue"}
        </button>
      </div>

      <div className="mt-4 rounded-3xl border border-white/10 bg-black/10 p-4">
        <label className="text-xs font-semibold uppercase tracking-[0.16em] text-white/45">
          Reviewer notes for single or bulk actions
        </label>
        <textarea
          value={reviewerNotes}
          onChange={(e) => setReviewerNotes(e.target.value)}
          rows={3}
          placeholder="Add reviewer notes"
          className="mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none placeholder:text-white/35"
        />
      </div>

      <div className="mt-4 flex flex-wrap gap-3">
        <button
          onClick={() => handleBulkAction("approve")}
          disabled={actionLoading}
          className="rounded-2xl border border-emerald-400/30 bg-emerald-400/10 px-5 py-3 text-sm font-semibold text-emerald-100 transition hover:bg-emerald-400/15 disabled:cursor-not-allowed disabled:opacity-60"
        >
          Bulk approve
        </button>
        <button
          onClick={() => handleBulkAction("reject")}
          disabled={actionLoading}
          className="rounded-2xl border border-rose-400/30 bg-rose-400/10 px-5 py-3 text-sm font-semibold text-rose-100 transition hover:bg-rose-400/15 disabled:cursor-not-allowed disabled:opacity-60"
        >
          Bulk reject
        </button>

        {statusMessage ? (
          <span className="self-center text-sm text-emerald-200">{statusMessage}</span>
        ) : null}

        {error ? (
          <span className="self-center text-sm text-red-200">{error}</span>
        ) : null}
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-3xl border border-white/10 bg-black/10 p-4">
          <div className="overflow-x-auto console-scrollbar">
            <table className="min-w-full border-separate border-spacing-y-2">
              <thead>
                <tr className="text-left text-xs uppercase tracking-[0.16em] text-white/45">
                  <th className="px-4 py-2">Select</th>
                  <th className="px-4 py-2">ID</th>
                  <th className="px-4 py-2">Run</th>
                  <th className="px-4 py-2">Status</th>
                  <th className="px-4 py-2">Priority</th>
                  <th className="px-4 py-2">Analysis</th>
                  <th className="px-4 py-2">Fetch mode</th>
                  <th className="px-4 py-2">Source</th>
                  <th className="px-4 py-2">Summary</th>
                </tr>
              </thead>
              <tbody>
                {queue.length === 0 ? (
                  <tr>
                    <td
                      colSpan={9}
                      className="rounded-2xl border border-white/10 bg-white/5 px-4 py-6 text-sm text-white/60"
                    >
                      No review items found for the selected filters.
                    </td>
                  </tr>
                ) : (
                  queue.map((item) => {
                    const analysisModeValue = getAnalysisMode(item);
                    const fetchModeValue = getFetchMode(item);
                    const sourceName = getSourceName(item);

                    return (
                      <tr
                        key={item.id}
                        className={`cursor-pointer text-sm transition ${
                          selectedItem?.id === item.id
                            ? "bg-cyan-400/10"
                            : "bg-white/5 hover:bg-white/7"
                        }`}
                        onClick={() => handleSelectDetail(item.id)}
                      >
                        <td
                          className="rounded-l-2xl px-4 py-3"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <input
                            type="checkbox"
                            checked={selectedIdSet.has(item.id)}
                            onChange={() => toggleSelection(item.id)}
                          />
                        </td>
                        <td className="px-4 py-3 font-medium text-white">{item.id}</td>
                        <td className="px-4 py-3 text-white/75">{item.scrape_run_id}</td>
                        <td className="px-4 py-3">{item.review_status}</td>
                        <td className="px-4 py-3">{item.priority_label ?? "N/A"}</td>
                        <td className="px-4 py-3">{analysisModeValue}</td>
                        <td className="px-4 py-3">
                          {fetchModeValue === "live" ? (
                            <span className="text-emerald-300">live</span>
                          ) : fetchModeValue === "stub" ? (
                            <span className="text-amber-300">stub</span>
                          ) : (
                            <span className="text-white/70">{fetchModeValue}</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-white/75">{sourceName}</td>
                        <td className="rounded-r-2xl px-4 py-3 text-white/70">
                          {item.source_summary?.slice(0, 110) ?? "N/A"}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="rounded-3xl border border-white/10 bg-black/10 p-5">
          {!selectedItem ? (
            <div className="text-sm text-white/60">
              Select a review item to inspect detail.
            </div>
          ) : (
            <div className="space-y-5">
              <div>
                <h3 className="text-lg font-semibold text-white">
                  Review item #{selectedItem.id}
                </h3>
                <p className="mt-2 text-sm leading-6 text-white/65">
                  {selectedItem.source_summary ?? "No summary available"}
                </p>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.16em] text-white/45">
                    Review status
                  </p>
                  <p className="mt-2 text-base font-semibold text-white">
                    {selectedItem.review_status}
                  </p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.16em] text-white/45">
                    Decision
                  </p>
                  <p className="mt-2 text-base font-semibold text-white">
                    {selectedItem.reviewer_decision ?? "Pending"}
                  </p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.16em] text-white/45">
                    Analysis mode
                  </p>
                  <p className="mt-2 text-base font-semibold text-white">
                    {getAnalysisMode(selectedItem)}
                  </p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.16em] text-white/45">
                    Fetch mode
                  </p>
                  <p className="mt-2 text-base font-semibold text-white">
                    {getFetchMode(selectedItem)}
                  </p>
                </div>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-white/45">
                  Insight snapshot
                </p>
                <div className="mt-3 space-y-2 text-sm text-white/72">
                  <p>
                    <span className="text-white/45">Pain point:</span>{" "}
                    {selectedItem.insight_snapshot?.pain_point_label ?? "N/A"}
                  </p>
                  <p>
                    <span className="text-white/45">Cluster:</span>{" "}
                    {selectedItem.insight_snapshot?.taxonomy_cluster ?? "N/A"}
                  </p>
                  <p>
                    <span className="text-white/45">Action:</span>{" "}
                    {selectedItem.insight_snapshot?.action_recommendation ?? "N/A"}
                  </p>
                  <p>
                    <span className="text-white/45">Confidence:</span>{" "}
                    {selectedItem.insight_snapshot?.confidence_score ?? "N/A"}
                  </p>
                  <p>
                    <span className="text-white/45">LLM attempted:</span>{" "}
                    {selectedItem.insight_snapshot?.llm_attempted === true
                      ? "Yes"
                      : selectedItem.insight_snapshot?.llm_attempted === false
                      ? "No"
                      : "N/A"}
                  </p>
                  <p>
                    <span className="text-white/45">LLM used:</span>{" "}
                    {selectedItem.insight_snapshot?.llm_used === true
                      ? "Yes"
                      : selectedItem.insight_snapshot?.llm_used === false
                      ? "No"
                      : "N/A"}
                  </p>
                </div>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-white/45">
                  Evidence snapshot
                </p>
                <div className="mt-3 space-y-2 text-sm text-white/72">
                  <p>
                    <span className="text-white/45">Source:</span>{" "}
                    {selectedItem.evidence_snapshot?.source_name ?? "N/A"}
                  </p>
                  <p>
                    <span className="text-white/45">Platform:</span>{" "}
                    {selectedItem.evidence_snapshot?.platform_name ?? "N/A"}
                  </p>
                  <p>
                    <span className="text-white/45">Content type:</span>{" "}
                    {selectedItem.evidence_snapshot?.content_type ?? "N/A"}
                  </p>
                  <p>
                    <span className="text-white/45">Excerpt:</span>{" "}
                    {selectedItem.evidence_snapshot?.evidence_excerpt ?? "N/A"}
                  </p>
                  <p>
                    <span className="text-white/45">Published at:</span>{" "}
                    {selectedItem.evidence_snapshot?.published_at ?? "N/A"}
                  </p>
                  <p>
                    <span className="text-white/45">Source URL:</span>{" "}
                    {selectedItem.evidence_snapshot?.source_url ?? "N/A"}
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap gap-3">
                <button
                  onClick={() => handleSingleAction("approve", selectedItem.id)}
                  disabled={actionLoading}
                  className="rounded-2xl border border-emerald-400/30 bg-emerald-400/10 px-5 py-3 text-sm font-semibold text-emerald-100 transition hover:bg-emerald-400/15 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  Approve item
                </button>
                <button
                  onClick={() => handleSingleAction("reject", selectedItem.id)}
                  disabled={actionLoading}
                  className="rounded-2xl border border-rose-400/30 bg-rose-400/10 px-5 py-3 text-sm font-semibold text-rose-100 transition hover:bg-rose-400/15 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  Reject item
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </SectionShell>
  );
}