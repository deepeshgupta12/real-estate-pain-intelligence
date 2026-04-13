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

function metricTone(value: string): string {
  if (value === "ready") return "text-emerald-300";
  if (value === "not_ready") return "text-amber-300";
  return "text-white";
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
      eyebrow="Active run"
      title="Current run summary"
      description="A cleaner snapshot of the active run, with identity, operational counts, readiness, and review-signal quality in one place."
    >
      {!currentRun ? (
        <div className="workspace-soft rounded-2xl px-4 py-6 text-sm text-white/58">
          No run is selected yet. Create a new run or load an existing run to begin.
        </div>
      ) : (
        <div className="space-y-5">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div className="workspace-soft rounded-2xl p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-white/40">
                Run ID
              </p>
              <p className="mt-2 text-2xl font-semibold text-white">
                #{currentRun.id}
              </p>
            </div>

            <div className="workspace-soft rounded-2xl p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-white/40">
                Brand
              </p>
              <p className="mt-2 text-2xl font-semibold text-white">
                {currentRun.target_brand}
              </p>
            </div>

            <div className="workspace-soft rounded-2xl p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-white/40">
                Status
              </p>
              <p className="mt-2 text-2xl font-semibold text-white">
                {humanize(currentRun.status)}
              </p>
            </div>

            <div className="workspace-soft rounded-2xl p-4">
              <div className="flex items-center gap-2">
                <p className="text-xs uppercase tracking-[0.16em] text-white/40">
                  Current stage
                </p>
                <InfoTip
                  title="Current stage"
                  description="This is the latest pipeline stage recorded for the run."
                />
              </div>
              <p className="mt-2 text-2xl font-semibold text-white">
                {humanize(currentRun.pipeline_stage)}
              </p>
            </div>
          </div>

          <div className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
            <div className="workspace-soft rounded-3xl p-5">
              <h3 className="text-lg font-semibold text-white">Run details</h3>

              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <div className="rounded-2xl border border-white/8 bg-white/2 px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.16em] text-white/38">
                    Source
                  </p>
                  <p className="mt-1 text-sm font-medium text-white/82">
                    {humanize(currentRun.source_name)}
                  </p>
                </div>

                <div className="rounded-2xl border border-white/8 bg-white/2 px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.16em] text-white/38">
                    Start type
                  </p>
                  <p className="mt-1 text-sm font-medium text-white/82">
                    {humanize(currentRun.trigger_mode)}
                  </p>
                </div>

                <div className="rounded-2xl border border-white/8 bg-white/2 px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.16em] text-white/38">
                    Items discovered
                  </p>
                  <p className="mt-1 text-sm font-medium text-white/82">
                    {currentRun.items_discovered}
                  </p>
                </div>

                <div className="rounded-2xl border border-white/8 bg-white/2 px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.16em] text-white/38">
                    Items processed
                  </p>
                  <p className="mt-1 text-sm font-medium text-white/82">
                    {currentRun.items_processed}
                  </p>
                </div>
              </div>

              <div className="mt-4 space-y-3">
                <div className="rounded-2xl border border-white/8 bg-white/2 px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.16em] text-white/38">
                    Latest note
                  </p>
                  <p className="mt-1 text-sm leading-6 text-white/74">
                    {currentRun.orchestrator_notes ?? "No note available"}
                  </p>
                </div>

                <div className="rounded-2xl border border-white/8 bg-white/2 px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.16em] text-white/38">
                    Last error
                  </p>
                  <p className="mt-1 text-sm leading-6 text-white/74">
                    {currentRun.error_message ?? "No error recorded"}
                  </p>
                </div>
              </div>
            </div>

            <div className="workspace-soft rounded-3xl p-5">
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-semibold text-white">
                  Readiness snapshot
                </h3>
                <InfoTip
                  title="Readiness snapshot"
                  description="This shows whether the run already has the outputs needed for downstream stages."
                />
              </div>

              {!readiness ? (
                <div className="mt-4 text-sm text-white/58">
                  Readiness details are not available yet.
                </div>
              ) : (
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-2xl border border-white/8 bg-white/2 p-4">
                    <p className="text-xs uppercase tracking-[0.16em] text-white/38">
                      Final state
                    </p>
                    <p
                      className={`mt-2 text-xl font-semibold ${metricTone(
                        readiness.ready_for_finalization ? "ready" : "not_ready",
                      )}`}
                    >
                      {readiness.ready_for_finalization ? "Ready" : "Not ready"}
                    </p>
                  </div>

                  <div className="rounded-2xl border border-white/8 bg-white/2 p-4">
                    <p className="text-xs uppercase tracking-[0.16em] text-white/38">
                      Evidence
                    </p>
                    <p className="mt-2 text-xl font-semibold text-white">
                      {readiness.counts.evidence_count}
                    </p>
                  </div>

                  <div className="rounded-2xl border border-white/8 bg-white/2 p-4">
                    <p className="text-xs uppercase tracking-[0.16em] text-white/38">
                      Insights
                    </p>
                    <p className="mt-2 text-xl font-semibold text-white">
                      {readiness.counts.insight_count}
                    </p>
                  </div>

                  <div className="rounded-2xl border border-white/8 bg-white/2 p-4">
                    <p className="text-xs uppercase tracking-[0.16em] text-white/38">
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

          <div className="workspace-soft rounded-3xl p-5">
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-semibold text-white">
                Review signal quality
              </h3>
              <InfoTip
                title="Review signal quality"
                description="These metrics are derived from the currently loaded review items for the active run."
              />
            </div>

            <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
              <div className="rounded-2xl border border-white/8 bg-white/2 p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-white/38">
                  Live-backed
                </p>
                <p className="mt-2 text-xl font-semibold text-emerald-300">
                  {liveCount}
                </p>
              </div>

              <div className="rounded-2xl border border-white/8 bg-white/2 p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-white/38">
                  Stub-backed
                </p>
                <p className="mt-2 text-xl font-semibold text-amber-300">
                  {stubCount}
                </p>
              </div>

              <div className="rounded-2xl border border-white/8 bg-white/2 p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-white/38">
                  Unknown mode
                </p>
                <p className="mt-2 text-xl font-semibold text-white">
                  {unknownCount}
                </p>
              </div>

              <div className="rounded-2xl border border-white/8 bg-white/2 p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-white/38">
                  LLM used
                </p>
                <p className="mt-2 text-xl font-semibold text-cyan-200">
                  {llmUsedCount}
                </p>
              </div>

              <div className="rounded-2xl border border-white/8 bg-white/2 p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-white/38">
                  Deterministic
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