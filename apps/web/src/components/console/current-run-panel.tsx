import { InfoTip } from "@/components/ui/info-tip";
import {
  ReviewQueueItem,
  RunReadinessResponse,
  ScrapeRunResponse,
} from "@/lib/api";
import { SectionShell } from "@/components/console/section-shell";

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

function getFetchMode(item: ReviewQueueItem): string {
  const evidenceMode = item.evidence_snapshot?.metadata_json?.fetch_mode;
  if (typeof evidenceMode === "string" && evidenceMode.trim()) {
    return evidenceMode;
  }

  const queueMode = item.metadata_json?.fetch_mode;
  if (typeof queueMode === "string" && queueMode.trim()) {
    return queueMode;
  }

  return "unknown";
}

export function CurrentRunPanel({
  currentRun,
  readiness,
  reviewQueue,
}: CurrentRunPanelProps) {
  const liveCount = reviewQueue.filter((item) => getFetchMode(item) === "live").length;
  const stubCount = reviewQueue.filter((item) => getFetchMode(item) === "stub").length;
  const unknownCount = reviewQueue.filter(
    (item) => !["live", "stub"].includes(getFetchMode(item)),
  ).length;

  const llmUsedCount = reviewQueue.filter(
    (item) => item.insight_snapshot?.llm_used === true,
  ).length;

  const deterministicCount = reviewQueue.filter(
    (item) => item.insight_snapshot?.llm_used !== true,
  ).length;

  return (
    <SectionShell
      id="current-run"
      eyebrow="Current context"
      title="Current run summary"
      description="A simple snapshot of the run you are currently working on, including stage, status, counts, readiness, and review-signal quality."
    >
      {!currentRun ? (
        <div className="rounded-2xl border border-white/10 bg-black/10 px-4 py-6 text-sm text-white/60">
          No run is selected yet. Create a new run or load an older one to begin.
        </div>
      ) : (
        <div className="space-y-5">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-2xl border border-white/10 bg-black/10 p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-white/45">
                Run ID
              </p>
              <p className="mt-2 text-2xl font-semibold text-white">
                #{currentRun.id}
              </p>
            </div>

            <div className="rounded-2xl border border-white/10 bg-black/10 p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-white/45">
                Brand name
              </p>
              <p className="mt-2 text-2xl font-semibold text-white">
                {currentRun.target_brand}
              </p>
            </div>

            <div className="rounded-2xl border border-white/10 bg-black/10 p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-white/45">
                Run status
              </p>
              <p className="mt-2 text-2xl font-semibold text-white">
                {humanize(currentRun.status)}
              </p>
            </div>

            <div className="rounded-2xl border border-white/10 bg-black/10 p-4">
              <div className="flex items-center gap-2">
                <p className="text-xs uppercase tracking-[0.16em] text-white/45">
                  Current stage
                </p>
                <InfoTip
                  title="Current stage"
                  description="This is the latest backend stage label for the run. It helps you understand what the system finished most recently."
                />
              </div>
              <p className="mt-2 text-2xl font-semibold capitalize text-white">
                {humanize(currentRun.pipeline_stage)}
              </p>
            </div>
          </div>

          <div className="grid gap-5 xl:grid-cols-[1fr_1fr]">
            <div className="rounded-3xl border border-white/10 bg-black/10 p-5">
              <h3 className="text-lg font-semibold text-white">Run details</h3>
              <div className="mt-4 space-y-3 text-sm text-white/72">
                <p>
                  <span className="text-white/45">Feedback source:</span>{" "}
                  {currentRun.source_name}
                </p>
                <p>
                  <span className="text-white/45">Start type:</span>{" "}
                  {currentRun.trigger_mode}
                </p>
                <p>
                  <span className="text-white/45">Items discovered:</span>{" "}
                  {currentRun.items_discovered}
                </p>
                <p>
                  <span className="text-white/45">Items processed:</span>{" "}
                  {currentRun.items_processed}
                </p>
                <p>
                  <span className="text-white/45">Latest note:</span>{" "}
                  {currentRun.orchestrator_notes ?? "No note available"}
                </p>
                <p>
                  <span className="text-white/45">Last error:</span>{" "}
                  {currentRun.error_message ?? "No error recorded"}
                </p>
              </div>
            </div>

            <div className="rounded-3xl border border-white/10 bg-black/10 p-5">
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-semibold text-white">Readiness snapshot</h3>
                <InfoTip
                  title="Readiness snapshot"
                  description="This shows whether the run already has the main outputs required for downstream stages like review, sync, exports, and final checks."
                />
              </div>

              {!readiness ? (
                <div className="mt-4 text-sm text-white/60">
                  Readiness details are not available yet.
                </div>
              ) : (
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <p className="text-xs uppercase tracking-[0.16em] text-white/45">
                      Final check
                    </p>
                    <p className="mt-2 text-xl font-semibold text-white">
                      {readiness.ready_for_finalization ? "Ready" : "Not ready"}
                    </p>
                  </div>

                  <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <p className="text-xs uppercase tracking-[0.16em] text-white/45">
                      Evidence collected
                    </p>
                    <p className="mt-2 text-xl font-semibold text-white">
                      {readiness.counts.evidence_count}
                    </p>
                  </div>

                  <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <p className="text-xs uppercase tracking-[0.16em] text-white/45">
                      Insights created
                    </p>
                    <p className="mt-2 text-xl font-semibold text-white">
                      {readiness.counts.insight_count}
                    </p>
                  </div>

                  <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <p className="text-xs uppercase tracking-[0.16em] text-white/45">
                      Review items
                    </p>
                    <p className="mt-2 text-xl font-semibold text-white">
                      {readiness.counts.review_count}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="rounded-3xl border border-white/10 bg-black/10 p-5">
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-semibold text-white">
                Review signal snapshot
              </h3>
              <InfoTip
                title="Review signal snapshot"
                description="This uses the currently loaded review items for the selected run to show whether signals came from live fetches or stub fallback, and whether insights actually used the LLM path."
              />
            </div>

            <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-white/45">
                  Live-backed items
                </p>
                <p className="mt-2 text-xl font-semibold text-emerald-300">
                  {liveCount}
                </p>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-white/45">
                  Stub-backed items
                </p>
                <p className="mt-2 text-xl font-semibold text-amber-300">
                  {stubCount}
                </p>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-white/45">
                  Unknown mode
                </p>
                <p className="mt-2 text-xl font-semibold text-white">
                  {unknownCount}
                </p>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-white/45">
                  LLM-used insights
                </p>
                <p className="mt-2 text-xl font-semibold text-cyan-200">
                  {llmUsedCount}
                </p>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-white/45">
                  Non-LLM insights
                </p>
                <p className="mt-2 text-xl font-semibold text-white">
                  {deterministicCount}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </SectionShell>
  );
}