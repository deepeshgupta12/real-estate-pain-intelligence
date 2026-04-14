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

const PAGE_SIZE = 20;

type StatusFilter = "all" | "pending" | "approved" | "rejected";

type ReviewConsolePanelProps = {
  initialRunId: number | null;
  activeRunId: number | null;
  initialSummary: ReviewSummaryResponse;
  initialQueue: ReviewQueueItem[];
};

function getItemStatus(item: ReviewQueueItem): StatusFilter {
  const decision = item.reviewer_decision ?? item.review_status ?? "pending";
  if (decision === "approved") return "approved";
  if (decision === "rejected") return "rejected";
  return "pending";
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
  const [queue, setQueue] = useState<ReviewQueueItem[]>(initialQueue);
  const [selectedItem, setSelectedItem] = useState<ReviewQueueItem | null>(null);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [reviewerNotes, setReviewerNotes] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("pending");

  const selectedIdSet = useMemo(() => new Set(selectedIds), [selectedIds]);

  // Compute live counts from queue state — always accurate after actions
  const liveCounts = useMemo(() => {
    const pending = queue.filter((i) => getItemStatus(i) === "pending").length;
    const approved = queue.filter((i) => getItemStatus(i) === "approved").length;
    const rejected = queue.filter((i) => getItemStatus(i) === "rejected").length;
    return { total: queue.length, pending, approved, rejected };
  }, [queue]);

  // Filtered items based on active status tab
  const filteredQueue = useMemo(() => {
    if (statusFilter === "all") return queue;
    return queue.filter((i) => getItemStatus(i) === statusFilter);
  }, [queue, statusFilter]);

  // Pagination derived values
  const totalPages = Math.max(1, Math.ceil(filteredQueue.length / PAGE_SIZE));
  const safePage = Math.min(currentPage, totalPages);
  const pageStart = (safePage - 1) * PAGE_SIZE;
  const pageEnd = pageStart + PAGE_SIZE;
  const pageItems = filteredQueue.slice(pageStart, pageEnd);
  const pageItemIds = pageItems.map((i) => i.id);
  const allPageSelected =
    pageItemIds.length > 0 && pageItemIds.every((id) => selectedIdSet.has(id));

  // Reset to page 1 and clear selection when filter changes
  useEffect(() => {
    setCurrentPage(1);
    setSelectedIds([]);
    setSelectedItem(null);
  }, [statusFilter]);

  // Reset page when queue length changes (after actions)
  useEffect(() => {
    setCurrentPage(1);
  }, [filteredQueue.length]);

  useEffect(() => {
    const nextRunValue = activeRunId ? String(activeRunId) : "";

    if (activeRunId === initialRunId) {
      setQueue(initialQueue);
      setSelectedItem(null);
      return;
    }

    let cancelled = false;

    async function syncToActiveRun() {
      try {
        const parsedRunId = nextRunValue ? Number(nextRunValue) : undefined;
        const [, queueData] = await Promise.all([
          fetchReviewSummary(parsedRunId),
          fetchReviewQueue({
            runId: parsedRunId,
            includeDetails: true,
            limit: 500,
            offset: 0,
          }),
        ]);

        if (cancelled) return;
        setQueue(queueData);
        setSelectedItem(null);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to sync review console");
        }
      }
    }

    void syncToActiveRun();
    return () => { cancelled = true; };
  }, [activeRunId, initialQueue, initialRunId]);

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
      setQueue((prev) =>
        prev.map((item) =>
          item.id === id
            ? { ...item, reviewer_decision: action === "approve" ? "approved" : "rejected" }
            : item
        )
      );
      setSelectedItem(null);
      setStatusMessage(action === "approve" ? "Item approved." : "Item rejected.");
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
        await bulkApproveReviewItems({ item_ids: selectedIds, reviewer_notes: reviewerNotes || undefined });
      } else {
        await bulkRejectReviewItems({ item_ids: selectedIds, reviewer_notes: reviewerNotes || undefined });
      }
      const decision = action === "approve" ? "approved" : "rejected";
      setQueue((prev) =>
        prev.map((item) =>
          selectedIds.includes(item.id) ? { ...item, reviewer_decision: decision } : item
        )
      );
      const count = selectedIds.length;
      setSelectedIds([]);
      setStatusMessage(`${count} items ${action}ed successfully.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bulk action failed");
    } finally {
      setActionLoading(false);
    }
  }

  function toggleSelection(id: number) {
    setSelectedIds((current) =>
      current.includes(id) ? current.filter((x) => x !== id) : [...current, id]
    );
  }

  function toggleSelectAll() {
    if (allPageSelected) {
      setSelectedIds((current) => current.filter((id) => !pageItemIds.includes(id)));
    } else {
      setSelectedIds((current) => {
        const merged = new Set(current);
        pageItemIds.forEach((id) => merged.add(id));
        return Array.from(merged);
      });
    }
  }

  function selectAllAcrossPages() {
    setSelectedIds(filteredQueue.map((i) => i.id));
  }

  function clearAllSelections() {
    setSelectedIds([]);
  }

  const FILTER_TABS: { key: StatusFilter; label: string; count: number; activeClass: string; dotClass: string }[] = [
    {
      key: "pending",
      label: "Pending",
      count: liveCounts.pending,
      activeClass: "border-amber-500 bg-amber-50 text-amber-700",
      dotClass: "bg-amber-400",
    },
    {
      key: "approved",
      label: "Approved",
      count: liveCounts.approved,
      activeClass: "border-green-500 bg-green-50 text-green-700",
      dotClass: "bg-green-500",
    },
    {
      key: "rejected",
      label: "Rejected",
      count: liveCounts.rejected,
      activeClass: "border-red-400 bg-red-50 text-red-700",
      dotClass: "bg-red-400",
    },
    {
      key: "all",
      label: "All",
      count: liveCounts.total,
      activeClass: "border-blue-500 bg-blue-50 text-blue-700",
      dotClass: "bg-blue-500",
    },
  ];

  return (
    <SectionShell
      id="review-console"
      eyebrow="Moderation"
      title="Review Queue"
      description="Approve or reject pain point findings"
    >
      <div className="space-y-4">
        {/* Live stat cards — click to filter */}
        <div className="grid gap-3 grid-cols-2 md:grid-cols-4">
          {FILTER_TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setStatusFilter(tab.key)}
              className={`card p-4 text-left transition hover:shadow-md ${
                statusFilter === tab.key ? "ring-2 ring-offset-1 ring-blue-400" : ""
              }`}
            >
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
                {tab.label}
              </p>
              <p className={`mt-2 text-2xl font-bold ${
                tab.key === "pending" ? "text-amber-600"
                : tab.key === "approved" ? "text-green-600"
                : tab.key === "rejected" ? "text-red-600"
                : "text-slate-900"
              }`}>
                {tab.count}
              </p>
              {statusFilter === tab.key && (
                <p className="mt-1 text-[10px] font-semibold text-blue-600 uppercase tracking-wide">
                  ← Viewing
                </p>
              )}
            </button>
          ))}
        </div>

        {/* Filter tabs */}
        <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-3">
          {FILTER_TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setStatusFilter(tab.key)}
              className={`inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-sm font-semibold transition ${
                statusFilter === tab.key
                  ? tab.activeClass + " shadow-sm"
                  : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
              }`}
            >
              <span className={`h-2 w-2 rounded-full ${statusFilter === tab.key ? tab.dotClass : "bg-slate-300"}`} />
              {tab.label}
              <span className={`ml-0.5 rounded-full px-1.5 py-0.5 text-[10px] font-bold ${
                statusFilter === tab.key ? "bg-white/70" : "bg-slate-100 text-slate-500"
              }`}>
                {tab.count}
              </span>
            </button>
          ))}
        </div>

        {queue.length === 0 ? (
          <div className="rounded-lg bg-slate-50 px-6 py-8 text-center text-slate-600">
            No review items yet. Run the analysis pipeline first.
          </div>
        ) : filteredQueue.length === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-6 py-10 text-center">
            <p className="text-2xl">
              {statusFilter === "pending" ? "🎉" : statusFilter === "approved" ? "✅" : "❌"}
            </p>
            <p className="mt-2 text-sm font-semibold text-slate-700">
              {statusFilter === "pending"
                ? "All caught up — no pending reviews!"
                : statusFilter === "approved"
                ? "No approved items yet"
                : statusFilter === "rejected"
                ? "No rejected items yet"
                : "No items"}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Switch tabs above to see other items.
            </p>
          </div>
        ) : (
          <>
            {/* Bulk action toolbar — only shown when pending tab is active */}
            {statusFilter === "pending" && (
              <div className="card p-5">
                <div className="flex flex-wrap items-center gap-3 mb-3">
                  <label className="flex items-center gap-2 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={allPageSelected}
                      onChange={toggleSelectAll}
                      className="h-4 w-4 rounded border-slate-300 accent-blue-600"
                    />
                    <span className="text-sm font-medium text-slate-700">
                      Select all on page
                    </span>
                  </label>

                  {filteredQueue.length > PAGE_SIZE && (
                    <button
                      onClick={selectAllAcrossPages}
                      className="text-xs text-blue-600 underline underline-offset-2 hover:text-blue-800"
                    >
                      Select all {filteredQueue.length} pending
                    </button>
                  )}

                  {selectedIds.length > 0 && (
                    <button
                      onClick={clearAllSelections}
                      className="text-xs text-slate-500 underline underline-offset-2 hover:text-slate-700"
                    >
                      Clear selection
                    </button>
                  )}

                  <span className="ml-auto text-sm text-slate-500">
                    {selectedIds.length > 0 ? `${selectedIds.length} selected` : "None selected"}
                  </span>
                </div>

                <div className="flex flex-wrap gap-3 mb-4">
                  <button
                    onClick={() => handleBulkAction("approve")}
                    disabled={selectedIds.length === 0 || actionLoading}
                    className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    ✓ Approve Selected ({selectedIds.length})
                  </button>
                  <button
                    onClick={() => handleBulkAction("reject")}
                    disabled={selectedIds.length === 0 || actionLoading}
                    className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    ✕ Reject Selected ({selectedIds.length})
                  </button>
                </div>

                <textarea
                  value={reviewerNotes}
                  onChange={(e) => setReviewerNotes(e.target.value)}
                  rows={2}
                  placeholder="Add reviewer notes for these decisions (optional)"
                  className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />

                {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
                {statusMessage && <p className="mt-2 text-sm text-green-600">{statusMessage}</p>}
              </div>
            )}

            {error && statusFilter !== "pending" && (
              <p className="text-sm text-red-600 px-1">{error}</p>
            )}
            {statusMessage && statusFilter !== "pending" && (
              <p className="text-sm text-green-600 px-1">{statusMessage}</p>
            )}

            {/* Pagination info + controls (top) */}
            <div className="flex items-center justify-between px-1">
              <p className="text-xs text-slate-500">
                Showing {pageStart + 1}–{Math.min(pageEnd, filteredQueue.length)} of{" "}
                {filteredQueue.length} {statusFilter === "all" ? "items" : `${statusFilter} items`}
              </p>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={safePage === 1}
                  className="rounded border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 disabled:opacity-40 hover:bg-slate-50"
                >
                  ← Prev
                </button>
                {Array.from({ length: totalPages }, (_, i) => i + 1)
                  .filter((p) => Math.abs(p - safePage) <= 2 || p === 1 || p === totalPages)
                  .reduce<(number | "…")[]>((acc, p, idx, arr) => {
                    if (idx > 0 && p - (arr[idx - 1] as number) > 1) acc.push("…");
                    acc.push(p);
                    return acc;
                  }, [])
                  .map((p, idx) =>
                    p === "…" ? (
                      <span key={`ellipsis-${idx}`} className="px-1 text-xs text-slate-400">…</span>
                    ) : (
                      <button
                        key={p}
                        onClick={() => setCurrentPage(p as number)}
                        className={`rounded border px-2.5 py-1 text-xs font-medium ${
                          p === safePage
                            ? "border-blue-500 bg-blue-600 text-white"
                            : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                        }`}
                      >
                        {p}
                      </button>
                    )
                  )}
                <button
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={safePage === totalPages}
                  className="rounded border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 disabled:opacity-40 hover:bg-slate-50"
                >
                  Next →
                </button>
              </div>
            </div>

            {/* Review items list */}
            <div className="space-y-3">
              {pageItems.map((item) => {
                const isSelected = selectedIdSet.has(item.id);
                const sourceName = getSourceName(item);
                const itemStatus = getItemStatus(item);

                return (
                  <div
                    key={item.id}
                    className={`card p-4 cursor-pointer transition ${
                      isSelected
                        ? "bg-blue-50 border-blue-300"
                        : itemStatus === "approved"
                        ? "bg-green-50/40 border-green-200"
                        : itemStatus === "rejected"
                        ? "bg-red-50/40 border-red-200"
                        : "hover:bg-slate-50"
                    }`}
                    onClick={() => setSelectedItem(item === selectedItem ? null : item)}
                  >
                    <div className="flex items-start gap-4">
                      {statusFilter === "pending" && (
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleSelection(item.id)}
                          onClick={(e) => e.stopPropagation()}
                          className="mt-1 h-4 w-4 rounded border-slate-300 accent-blue-600 shrink-0"
                        />
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="font-semibold text-slate-900 text-sm">#{item.id}</p>
                          <span className="status-pill info">{humanize(sourceName)}</span>
                          <span
                            className={`status-pill ${
                              itemStatus === "approved"
                                ? "success"
                                : itemStatus === "rejected"
                                ? "error"
                                : "warning"
                            }`}
                          >
                            {itemStatus === "pending" ? "⏳ Pending" : itemStatus === "approved" ? "✓ Approved" : "✕ Rejected"}
                          </span>
                        </div>
                        <p className="text-sm text-slate-600 mt-2 line-clamp-2">
                          {item.source_summary ?? "No summary"}
                        </p>
                      </div>
                    </div>

                    {/* Inline action row for pending items */}
                    {selectedItem?.id === item.id && (
                      <div className="mt-4 pt-4 border-t border-slate-200">
                        <div className="space-y-3 text-sm mb-4">
                          {item.source_summary && (
                            <p className="text-slate-700 leading-relaxed">{item.source_summary}</p>
                          )}
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <p className="text-xs text-slate-500 font-semibold uppercase">Status</p>
                              <p className="text-slate-900 mt-0.5">{humanize(item.review_status)}</p>
                            </div>
                            <div>
                              <p className="text-xs text-slate-500 font-semibold uppercase">Priority</p>
                              <p className="text-slate-900 mt-0.5">{humanize(item.priority_label)}</p>
                            </div>
                          </div>
                        </div>
                        {itemStatus === "pending" && (
                          <div className="flex gap-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                void handleSingleAction("approve", item.id);
                              }}
                              disabled={actionLoading}
                              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex-1 text-sm"
                            >
                              ✓ Approve
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                void handleSingleAction("reject", item.id);
                              }}
                              disabled={actionLoading}
                              className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed flex-1 text-sm"
                            >
                              ✕ Reject
                            </button>
                          </div>
                        )}
                        {itemStatus !== "pending" && (
                          <p className="text-xs text-slate-400 italic">
                            This item has already been {itemStatus}. Switch to the Pending tab to take action.
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Pagination bottom */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 pt-2">
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={safePage === 1}
                  className="rounded border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 disabled:opacity-40 hover:bg-slate-50"
                >
                  ← Previous page
                </button>
                <span className="text-xs text-slate-500">Page {safePage} of {totalPages}</span>
                <button
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={safePage === totalPages}
                  className="rounded border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 disabled:opacity-40 hover:bg-slate-50"
                >
                  Next page →
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </SectionShell>
  );
}
