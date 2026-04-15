import {
  ReviewQueueItem,
  RunReadinessResponse,
  ScrapeRunResponse,
} from "@/lib/api";
import { SectionShell } from "@/components/console/section-shell";
import { formatSourceIcons, formatSourceLabel } from "@/components/console/run-setup-panel";

type CurrentRunPanelProps = {
  currentRun: ScrapeRunResponse | null;
  readiness: RunReadinessResponse | null;
  reviewQueue: ReviewQueueItem[];
};

function humanize(value: string | null | undefined): string {
  if (!value) {
    return "Not available";
  }

  return value.replaceAll("_", " ");
}

export function CurrentRunPanel({
  currentRun,
  readiness,
  reviewQueue: _reviewQueue,
}: CurrentRunPanelProps) {
  return (
    <SectionShell
      id="current-run"
      eyebrow="Status"
      title="Current Session"
      description="Overview of the active research session"
    >
      {!currentRun ? (
        <div className="rounded-lg bg-slate-50 px-6 py-8 text-center text-slate-600">
          No session selected yet. Create or load one to begin.
        </div>
      ) : (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="card p-4">
              <p className="text-xs font-semibold text-slate-600 uppercase">Platform</p>
              <p className="mt-1 text-base font-semibold text-slate-900">
                {formatSourceIcons(currentRun.source_name)}{" "}
                {formatSourceLabel(currentRun.source_name)}
              </p>
            </div>

            <div className="card p-4">
              <p className="text-xs font-semibold text-slate-600 uppercase">Brand</p>
              <p className="mt-2 text-lg font-semibold text-slate-900">{currentRun.target_brand}</p>
            </div>

            <div className="card p-4">
              <p className="text-xs font-semibold text-slate-600 uppercase">Status</p>
              <p className="mt-2">
                <span className="status-pill success">{humanize(currentRun.status)}</span>
              </p>
            </div>

            <div className="card p-4">
              <p className="text-xs font-semibold text-slate-600 uppercase">Current Step</p>
              <p className="mt-2 text-sm font-semibold text-slate-900">{humanize(currentRun.pipeline_stage)}</p>
            </div>
          </div>

          <div className="card p-6">
            <h3 className="font-semibold text-slate-900 mb-4">Session Details</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <p className="text-sm text-slate-600">Posts Collected</p>
                <p className="text-2xl font-semibold text-slate-900 mt-1">{currentRun.items_discovered}</p>
              </div>
              <div>
                <p className="text-sm text-slate-600">Posts Processed</p>
                <p className="text-2xl font-semibold text-slate-900 mt-1">{currentRun.items_processed}</p>
              </div>
            </div>
            {currentRun.session_notes && (
              <div className="mt-4 pt-4 border-t border-slate-200">
                <p className="text-xs font-semibold uppercase text-slate-500">Session Notes</p>
                <p className="text-sm text-slate-700 mt-1 italic">💬 {currentRun.session_notes}</p>
              </div>
            )}
            {currentRun.orchestrator_notes && (
              <div className="mt-4 pt-4 border-t border-slate-200">
                <p className="text-xs font-semibold uppercase text-slate-500">Pipeline Status</p>
                <p className="text-sm text-slate-700 mt-1">{currentRun.orchestrator_notes}</p>
              </div>
            )}
            {currentRun.error_message && (
              <div className="mt-4 pt-4 border-t border-red-200 bg-red-50 p-3 rounded text-sm text-red-700">
                Error: {currentRun.error_message}
              </div>
            )}
          </div>

          {readiness && (
            <div className="card p-6">
              <h3 className="font-semibold text-slate-900 mb-4">Readiness</h3>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="text-center">
                  <p className="text-sm text-slate-600">Posts</p>
                  <p className="text-2xl font-semibold text-slate-900 mt-1">{readiness.counts.evidence_count}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-slate-600">Pain Points</p>
                  <p className="text-2xl font-semibold text-slate-900 mt-1">{readiness.counts.insight_count}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-slate-600">Review Items</p>
                  <p className="text-2xl font-semibold text-slate-900 mt-1">{readiness.counts.review_count}</p>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-slate-200">
                <span className={`status-pill ${readiness.ready_for_finalization ? "success" : "warning"}`}>
                  {readiness.ready_for_finalization ? "Ready for export" : "In progress"}
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </SectionShell>
  );
}