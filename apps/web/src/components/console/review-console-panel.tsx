"use client";

import { useMemo, useState } from "react";
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
  initialSummary: ReviewSummaryResponse;
  initialQueue: ReviewQueueItem[];
};

export function ReviewConsolePanel({
  initialSummary,
  initialQueue,
}: ReviewConsolePanelProps) {
  const [summary, setSummary] = useState<ReviewSummaryResponse>(initialSummary);
  const [queue, setQueue] = useState<ReviewQueueItem[]>(initialQueue);
  const [selectedItem, setSelectedItem] = useState<ReviewQueueItem | null>(
    initialQueue[0] ?? null,
  );
  const [runId, setRunId] = useState("");
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

  async function reloadData() {
    const parsedRunId = runId ? Number(runId) : undefined;

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

  async function handleLoadQueue() {
    setLoading(true);
    setError("");
    setStatusMessage("");

    try {
      await reloadData();
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
        action === "approve" ? "Review item approved successfully." : "Review item rejected successfully.",
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
      current.includes(id) ? current.filter((itemId) => itemId !== id) : [...current, id],
    );
  }

  return (
    <SectionShell
      id="review-console"
      eyebrow="Human validation"
      title="Review console"
      description="Review summary, filtered queue, joined detail, and single or bulk moderation actions for agent-generated insights."
    >
      <div className="grid gap-4 md:grid-cols-4">
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

      <div className="mt-5 grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-3xl border border-white/10 bg-black/10 p-4">
          <div className="overflow-x-auto console-scrollbar">
            <table className="min-w-full border-separate border-spacing-y-2">
              <thead>
                <tr className="text-left text-xs uppercase tracking-[0.16em] text-white/45">
                  <th className="px-4 py-2">Select</th>
                  <th className="px-4 py-2">ID</th>
                  <th className="px-4 py-2">Status</th>
                  <th className="px-4 py-2">Priority</th>
                  <th className="px-4 py-2">Analysis</th>
                  <th className="px-4 py-2">Summary</th>
                </tr>
              </thead>
              <tbody>
                {queue.length === 0 ? (
                  <tr>
                    <td
                      colSpan={6}
                      className="rounded-2xl border border-white/10 bg-white/5 px-4 py-6 text-sm text-white/60"
                    >
                      No review items found for the selected filters.
                    </td>
                  </tr>
                ) : (
                  queue.map((item) => {
                    const analysisModeValue =
                      String(item.metadata_json?.analysis_mode ?? "");

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
                        <td className="px-4 py-3">{item.review_status}</td>
                        <td className="px-4 py-3">{item.priority_label ?? "N/A"}</td>
                        <td className="px-4 py-3">{analysisModeValue || "N/A"}</td>
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
                    <span className="text-white/45">Excerpt:</span>{" "}
                    {selectedItem.evidence_snapshot?.evidence_excerpt ?? "N/A"}
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