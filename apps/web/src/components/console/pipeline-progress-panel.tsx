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
    return "border-emerald-400/18 bg-emerald-400/10";
  }

  if (status === "current") {
    return "border-cyan-400/18 bg-cyan-400/10";
  }

  return "border-white/8 bg-white/[0.025]";
}

function labelForStatus(status: StageStatus): string {
  if (status === "completed") return "Done";
  if (status === "current") return "Current";
  return "Pending";
}

function badgeTone(status: StageStatus): string {
  if (status === "completed") return "badge badge-success";
  if (status === "current") return "badge badge-info";
  return "badge badge-neutral";
}

export function PipelineProgressPanel({
  currentRun,
  readiness,
}: PipelineProgressPanelProps) {
  const counts = readiness?.counts;
  const checks = readiness?.checks;

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
      description: "A run exists and is ready to be operated.",
      done: completionFlags[0],
    },
    {
      title: "Collect feedback",
      description: "Bring raw public feedback into the workspace.",
      done: completionFlags[1],
    },
    {
      title: "Clean text",
      description: "Normalize the collected content into stable inputs.",
      done: completionFlags[2],
    },
    {
      title: "Prepare language",
      description: "Resolve multilingual and script-related signals.",
      done: completionFlags[3],
    },
    {
      title: "Generate insights",
      description: "Turn evidence into structured pain-point output.",
      done: completionFlags[4],
    },
    {
      title: "Build search library",
      description: "Create retrieval-ready documents for later querying.",
      done: completionFlags[5],
    },
    {
      title: "Create review list",
      description: "Prepare moderation-ready review queue items.",
      done: completionFlags[6],
    },
    {
      title: "Prepare Notion sync",
      description: "Generate sync jobs for approved items.",
      done: completionFlags[7],
    },
    {
      title: "Create exports",
      description: "Generate CSV, JSON, and PDF output.",
      done: completionFlags[8],
    },
    {
      title: "Final readiness",
      description: "Confirm run completeness across the pipeline.",
      done: completionFlags[9],
    },
  ];

  return (
    <SectionShell
      id="pipeline-progress"
      eyebrow="Stage tracker"
      title="Pipeline progress"
      description="A more readable view of where the active run stands, based on actual generated outputs rather than only the latest stage label."
    >
      {!currentRun ? (
        <div className="workspace-soft rounded-2xl px-4 py-6 text-sm text-white/58">
          Pick a run first to see pipeline progress.
        </div>
      ) : (
        <>
          <div className="workspace-soft mb-5 rounded-3xl p-5">
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-semibold text-white">
                How to read this
              </h3>
              <InfoTip
                title="How this works"
                description="The tracker marks steps as completed when their key outputs exist for the active run."
              />
            </div>

            <p className="mt-3 text-sm leading-6 text-white/60">
              The current step is the first unfinished stage. This keeps the
              tracker aligned with actual backend state instead of relying only
              on one stage string.
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
                      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/38">
                        Step {String(index + 1).padStart(2, "0")}
                      </p>
                      <h3 className="mt-2 text-lg font-semibold text-white">
                        {stage.title}
                      </h3>
                    </div>

                    <span className={badgeTone(status)}>{labelForStatus(status)}</span>
                  </div>

                  <p className="mt-3 text-sm leading-6 text-white/62">
                    {stage.description}
                  </p>
                </div>
              );
            })}
          </div>

          {checks ? (
            <div className="workspace-soft mt-5 rounded-3xl p-5">
              <h3 className="text-lg font-semibold text-white">Readiness checks</h3>

              <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {Object.entries(checks).map(([key, value]) => (
                  <div
                    key={key}
                    className="flex items-center justify-between rounded-2xl border border-white/8 bg-white/2 px-4 py-3 text-sm"
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