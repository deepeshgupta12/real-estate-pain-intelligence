import { InfoTip } from "@/components/ui/info-tip";
import { RunReadinessResponse, ScrapeRunResponse } from "@/lib/api";
import { SectionShell } from "@/components/console/section-shell";

type PipelineProgressPanelProps = {
  currentRun: ScrapeRunResponse | null;
  readiness: RunReadinessResponse | null;
};

type StageStatus = "completed" | "current" | "upcoming";

function toneForStatus(status: StageStatus): string {
  if (status === "completed") {
    return "border-emerald-400/25 bg-emerald-400/10";
  }

  if (status === "current") {
    return "border-cyan-400/25 bg-cyan-400/10";
  }

  return "border-white/10 bg-white/5";
}

function labelForStatus(status: StageStatus): string {
  if (status === "completed") {
    return "Done";
  }

  if (status === "current") {
    return "Next focus";
  }

  return "Pending";
}

export function PipelineProgressPanel({
  currentRun,
  readiness,
}: PipelineProgressPanelProps) {
  const checks = readiness?.checks;
  const counts = readiness?.counts;

  const completionFlags = [
    Boolean(currentRun),
    (counts?.evidence_count ?? 0) > 0,
    (counts?.normalized_count ?? 0) > 0,
    (counts?.multilingual_count ?? 0) > 0,
    (counts?.insight_count ?? 0) > 0,
    (counts?.retrieval_count ?? 0) > 0,
    (counts?.review_count ?? 0) > 0,
    (counts?.notion_sync_count ?? 0) > 0,
    (counts?.export_count ?? 0) > 0,
    Boolean(readiness?.ready_for_finalization),
  ];

  const firstPendingIndex = completionFlags.findIndex((flag) => !flag);

  const stages = [
    {
      title: "Run setup",
      description: "A run exists and is ready for stage actions.",
      done: completionFlags[0],
    },
    {
      title: "Collect public feedback",
      description: "Bring raw comments, reviews, or posts into the workspace.",
      done: completionFlags[1],
    },
    {
      title: "Clean text",
      description: "Prepare the raw text so the downstream steps work with cleaner inputs.",
      done: completionFlags[2],
    },
    {
      title: "Prepare language support",
      description: "Resolve language and script signals for multilingual understanding.",
      done: completionFlags[3],
    },
    {
      title: "Generate insights",
      description: "Turn user feedback into pain points, root causes, priority labels, and actions.",
      done: completionFlags[4],
    },
    {
      title: "Prepare search-ready library",
      description: "Make the processed run searchable for later analysis and exploration.",
      done: completionFlags[5],
    },
    {
      title: "Create review list",
      description: "Prepare a human-review queue so the team can validate or reject outputs.",
      done: completionFlags[6],
    },
    {
      title: "Prepare Notion sync",
      description: "Create the jobs needed for approved items to be sent into Notion.",
      done: completionFlags[7],
    },
    {
      title: "Create downloadable files",
      description: "Generate CSV, JSON, or PDF outputs for the run.",
      done: completionFlags[8],
    },
    {
      title: "Final readiness check",
      description: "Confirm the run has the main outputs needed across the pipeline.",
      done: completionFlags[9],
    },
  ];

  return (
    <SectionShell
      id="pipeline-progress"
      eyebrow="Progress view"
      title="Pipeline progress"
      description="A simple stage tracker that translates the backend workflow into easy-to-understand progress steps."
    >
      {!currentRun ? (
        <div className="rounded-2xl border border-white/10 bg-black/10 px-4 py-6 text-sm text-white/60">
          Pick a run first to see progress across the full pipeline.
        </div>
      ) : (
        <>
          <div className="mb-5 rounded-3xl border border-white/10 bg-black/10 p-5">
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-semibold text-white">
                How to read this tracker
              </h3>
              <InfoTip
                title="How this tracker works"
                description="Each stage becomes completed as soon as its main output exists. The first unfinished stage is shown as the next focus."
              />
            </div>
            <p className="mt-3 text-sm leading-6 text-white/65">
              The tracker does not depend only on the last stage label. It also
              uses the actual outputs already created for the current run.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {stages.map((stage, index) => {
              let status: StageStatus = "upcoming";

              if (stage.done) {
                status = "completed";
              } else if (firstPendingIndex === index) {
                status = "current";
              }

              return (
                <div
                  key={stage.title}
                  className={`rounded-3xl border p-5 ${toneForStatus(status)}`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/45">
                        Step {String(index + 1).padStart(2, "0")}
                      </p>
                      <h3 className="mt-2 text-lg font-semibold text-white">
                        {stage.title}
                      </h3>
                    </div>

                    <span className="rounded-full border border-white/10 bg-black/20 px-2 py-1 text-[10px] uppercase tracking-wide text-white/70">
                      {labelForStatus(status)}
                    </span>
                  </div>

                  <p className="mt-3 text-sm leading-6 text-white/65">
                    {stage.description}
                  </p>
                </div>
              );
            })}
          </div>

          {checks ? (
            <div className="mt-5 rounded-3xl border border-white/10 bg-black/10 p-5">
              <h3 className="text-lg font-semibold text-white">Readiness checks</h3>
              <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {Object.entries(checks).map(([key, value]) => (
                  <div
                    key={key}
                    className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm"
                  >
                    <span className="text-white/70">{key.replaceAll("_", " ")}</span>
                    <span className={value ? "text-emerald-300" : "text-amber-300"}>
                      {value ? "Yes" : "No"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </>
      )}
    </SectionShell>
  );
}