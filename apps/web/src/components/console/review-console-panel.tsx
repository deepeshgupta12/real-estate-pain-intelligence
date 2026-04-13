"use client";

import { useEffect, useMemo, useState } from "react";
import {
  approveReviewItem,
  bulkApproveReviewItems,
  bulkRejectReviewItems,
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

function getSourceName(item: ReviewQueueItem): string {
  return (
    item.evidence_snapshot?.source_name ||
    (typeof item.metadata_json?.source_name === "string"
      ? item.metadata_json.source_name
      : "") ||
    "N/A"
  );
}

function humanize(value: string | null | undefined): string {
  if (!value) return "N/A";
  return value.replaceAll("_", " ");
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
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [reviewerNotes, setReviewerNotes] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");

  const selectedIdSet = useMemo(() => new Set(selectedIds), [selectedIds]);

  useEffect(() => {
    const nextRunValue = activeRunId ? String(activeRunId) : "";

    if (activeRunId === initialRunId) {
      setSummary(initialSummary);
      setQueue(initialQueue);
      setSelectedItem(initialQueue[0] ?? null);
      return;
    }

    let cancelled = false;

    async function syncToActiveRun() {
      try {
        const parsedRunId = nextRunValue ? Number(nextRunValue) : undefined;
        const [summaryData, queueData] = await Promise.all([
          fetchReviewSummary(parsedRunId),
          fetchReviewQueue({
            runId: parsedRunId,
            includeDetails: true,
            limit: 50,
            offset: 0,
          }),
        ]);

        if (cancelled) return;

        setSummary(summaryData);
        setQueue(queueData);
        setSelectedItem(queueData[0] ?? null);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to sync review console"
          );
        }
      }
    }

    void syncToActiveRun();

    return () => {
      cancelled = true;
    };
  }, [activeRunId, initialQueue, initialRunId, initialSummary]);

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

      const updatedQueue = queue.map((item) =>
        item.id === id
          ? {
              ...item,
              reviewer_decision: action === "approve" ? "approved" : "rejected",
            }
          : item
      );
      setQueue(updatedQueue);
      setSelectedItem(updatedQueue.find((item) => item.id === id) ?? null);

      setStatusMessage(
        action === "approve"
          ? "Item approved successfully."
          : "Item rejected successfully."
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleBulkAction(action: "approve" | "reject") {
    if (selectedIds.length === 0) {
      setError("Select at least one item.");
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

      const decision = action === "approve" ? "approved" : "rejected";
      const updatedQueue = queue.map((item) =>
        selectedIds.includes(item.id) ? { ...item, reviewer_decision: decision } : item
      );
      setQueue(updatedQueue);
      setSelectedIds([]);

      setStatusMessage(`${selectedIds.length} items ${action}ed successfully.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bulk action failed");
    } finally {
      setActionLoading(false);
    }
  }

  function toggleSelection(id: number) {
    setSelectedIds((current) =>
      current.includes(id)
        ? current.filter((itemId) => itemId !== id)
        : [...current, id]
    );
  }

  return (
    <SectionShell
      id="review-console"
      eyebrow="Moderation"
      title="Review Queue"
      description="Approve or reject pain point findings"
    >
      <div className="space-y-4">
        <div className="grid gap-4 md:grid-cols-4">
          <div className="card p-4">
            <p className="text-xs font-semibold text-slate-600 uppercase">Total</p>
            <p className="mt-2 text-2xl font-semibold text-slate-900">{summary.total_items}</p>
          </div>
          <div className="card p-4">
            <p className="text-xs font-semibold text-slate-600 uppercase">Pending</p>
            <p className="mt-2 text-2xl font-semibold text-yellow-600">{summary.pending_review_count}</p>
          </div>
          <div className="card p-4">
            <p className="text-xs font-semibold text-slate-600 uppercase">Approved</p>
            <p className="mt-2 text-2xl font-semibold text-green-600">{summary.approved_count}</p>
          </div>
          <div className="card p-4">
            <p className="text-xs font-semibold text-slate-600 uppercase">Rejected</p>
            <p className="mt-2 text-2xl font-semibold text-red-600">{summary.rejected_count}</p>
          </div>
        </div>

        {queue.length === 0 ? (
          <div className="rounded-lg bg-slate-50 px-6 py-8 text-center text-slate-600">
            No review items yet. Run the analysis first.
          </div>
        ) : (
          <>
            <div className="card p-6">
              <div className="flex flex-wrap gap-3 mb-4">
                <button
                  onClick={() => handleBulkAction("approve")}
                  disabled={selectedIds.length === 0 || actionLoading}
                  className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Approve Selected
                </button>
                <button
                  onClick={() => handleBulkAction("reject")}
                  disabled={selectedIds.length === 0 || actionLoading}
                  className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Reject Selected
                </button>
                <span className="text-sm text-slate-600 self-center">
                  {selectedIds.length} selected
                </span>
              </div>

              <textarea
                value={reviewerNotes}
                onChange={(e) => setReviewerNotes(e.target.value)}
                rows={2}
                placeholder="Add notes for these decisions"
                className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />

              {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
              {statusMessage && <p className="mt-2 text-sm text-green-600">{statusMessage}</p>}
            </div>

            <div className="space-y-3">
              {queue.map((item) => {
                const isSelected = selectedIdSet.has(item.id);
                const sourceName = getSourceName(item);
                const decision = item.reviewer_decision ?? item.review_status;

                return (
                  <div
                    key={item.id}
                    className={`card p-4 cursor-pointer transition ${
                      isSelected ? "bg-blue-50 border-blue-300" : "hover:bg-slate-50"
                    }`}
                    onClick={() => setSelectedItem(item)}
                  >
                    <div className="flex items-start gap-4">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleSelection(item.id)}
                        onClick={(e) => e.stopPropagation()}
                        className="mt-1"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="font-semibold text-slate-900">#{item.id}</p>
                          <span className="status-pill info">{humanize(sourceName)}</span>
                          <span
                            className={`status-pill ${
                              decision === "approved"
                                ? "success"
                                : decision === "rejected"
                                ? "error"
                                : "warning"
                            }`}
                          >
                            {humanize(decision)}
                          </span>
                        </div>
                        <p className="text-sm text-slate-600 mt-2 line-clamp-2">
                          {item.source_summary ?? "No summary"}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {selectedItem && (
              <div className="card p-6 bg-blue-50">
                <h3 className="font-semibold text-slate-900 mb-4">Details: Item #{selectedItem.id}</h3>
                <div className="space-y-3 text-sm">
                  <p><span className="font-medium text-slate-700">Summary:</span> {selectedItem.source_summary}</p>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-slate-600 font-semibold">Status</p>
                      <p className="text-slate-900">{humanize(selectedItem.review_status)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-600 font-semibold">Priority</p>
                      <p className="text-slate-900">{humanize(selectedItem.priority_label)}</p>
                    </div>
                  </div>
                </div>

                <div className="mt-4 flex gap-2">
                  <button
                    onClick={() => handleSingleAction("approve", selectedItem.id)}
                    disabled={actionLoading}
                    className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex-1"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => handleSingleAction("reject", selectedItem.id)}
                    disabled={actionLoading}
                    className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed flex-1"
                  >
                    Reject
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </SectionShell>
  );
}
