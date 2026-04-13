import {
  RunReadinessResponse,
  ScrapeRunResponse,
} from "@/lib/api";
import { SectionShell } from "@/components/console/section-shell";

type PipelineProgressPanelProps = {
  currentRun: ScrapeRunResponse | null;
  readiness: RunReadinessResponse | null;
};

function humanize(value: string | null | undefined): string {
  if (!value) return "Unknown";
  return value.replaceAll("_", " ");
}

const steps = [
  { stage: "created", label: "Created", icon: "📋" },
  { stage: "dispatched", label: "Dispatched", icon: "🚀" },
  { stage: "scraping", label: "Collecting", icon: "📥" },
  { stage: "scraping_completed", label: "Collection Done", icon: "✓" },
  { stage: "normalization_completed", label: "Cleaned", icon: "✓" },
  { stage: "multilingual_completed", label: "Detected Languages", icon: "✓" },
  { stage: "intelligence_completed", label: "Analyzed", icon: "✓" },
  { stage: "retrieval_indexed", label: "Indexed", icon: "✓" },
  { stage: "review_queued", label: "Review Ready", icon: "✓" },
  { stage: "exports_generated", label: "Exported", icon: "✓" },
];

export function PipelineProgressPanel({
  currentRun,
  readiness,
}: PipelineProgressPanelProps) {
  if (!currentRun) {
    return (
      <SectionShell
        id="pipeline-progress"
        eyebrow="Timeline"
        title="Pipeline Progress"
        description="Track the research session through each step"
      >
        <div className="rounded-lg bg-slate-50 px-6 py-8 text-center text-slate-600">
          No session selected yet.
        </div>
      </SectionShell>
    );
  }

  const currentStageIndex = steps.findIndex((s) => s.stage === currentRun.pipeline_stage);

  return (
    <SectionShell
      id="pipeline-progress"
      eyebrow="Timeline"
      title="Pipeline Progress"
      description="Track the research session through each step"
    >
      <div className="card p-6">
        <div className="space-y-4">
          {steps.map((step, index) => {
            const isCompleted = index < currentStageIndex;
            const isCurrent = index === currentStageIndex;
            const isPending = index > currentStageIndex;

            return (
              <div key={step.stage} className="flex items-center gap-4">
                <div
                  className={`flex h-8 w-8 items-center justify-center rounded-full shrink-0 text-sm font-semibold ${
                    isCompleted
                      ? "bg-green-100 text-green-700"
                      : isCurrent
                      ? "bg-blue-100 text-blue-700"
                      : "bg-slate-100 text-slate-400"
                  }`}
                >
                  {isCompleted ? "✓" : isCurrent ? step.icon : `${index + 1}`}
                </div>
                <div className="flex-1">
                  <p
                    className={`font-medium ${
                      isCurrent
                        ? "text-slate-900 font-semibold"
                        : isCompleted
                        ? "text-green-700"
                        : "text-slate-500"
                    }`}
                  >
                    {step.label}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {readiness && (
          <div className="mt-6 pt-6 border-t border-slate-200">
            <p className="text-sm font-medium text-slate-900">Counts:</p>
            <div className="mt-3 grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-2xl font-semibold text-slate-900">{readiness.counts.evidence_count}</p>
                <p className="text-xs text-slate-600 mt-1">Posts</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-semibold text-slate-900">{readiness.counts.insight_count}</p>
                <p className="text-xs text-slate-600 mt-1">Pain Points</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-semibold text-slate-900">{readiness.counts.review_count}</p>
                <p className="text-xs text-slate-600 mt-1">Review Items</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </SectionShell>
  );
}
