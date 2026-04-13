"use client";

import { SectionShell } from "@/components/console/section-shell";

export type PipelineActionKey =
  | "collect_feedback"
  | "clean_text"
  | "prepare_language"
  | "generate_insights"
  | "build_search_library"
  | "create_review_list"
  | "prepare_notion_sync"
  | "run_notion_sync"
  | "create_exports"
  | "check_readiness"
  | "refresh_workspace";

type PipelineActionsPanelProps = {
  currentRunId: number | null;
  actionLoadingKey: PipelineActionKey | null;
  onAction: (action: PipelineActionKey) => Promise<void>;
};

const steps: Array<{
  key: PipelineActionKey;
  title: string;
  description: string;
  buttonLabel: string;
}> = [
  {
    key: "collect_feedback",
    title: "Step 1: Collect Posts",
    description: "Gather feedback from the selected platform",
    buttonLabel: "Run Now →",
  },
  {
    key: "clean_text",
    title: "Step 2: Clean & Detect",
    description: "Normalize content and detect languages",
    buttonLabel: "Run Now →",
  },
  {
    key: "prepare_language",
    title: "Step 3: Language Support",
    description: "Prepare multilingual content",
    buttonLabel: "Run Now →",
  },
  {
    key: "generate_insights",
    title: "Step 4: Analyze",
    description: "Generate pain point analysis",
    buttonLabel: "Run Now →",
  },
  {
    key: "build_search_library",
    title: "Step 5: Index",
    description: "Make results searchable",
    buttonLabel: "Run Now →",
  },
  {
    key: "create_review_list",
    title: "Step 6: Build Queue",
    description: "Prepare review items",
    buttonLabel: "Run Now →",
  },
  {
    key: "create_exports",
    title: "Step 7: Export",
    description: "Download results as CSV, JSON, PDF",
    buttonLabel: "Download",
  },
];

export function PipelineActionsPanel({
  currentRunId,
  actionLoadingKey,
  onAction,
}: PipelineActionsPanelProps) {
  const isLoading = actionLoadingKey !== null;

  return (
    <SectionShell
      id="pipeline-actions"
      eyebrow="Automation"
      title="Pipeline Steps"
      description="Execute each step of the research process in order"
    >
      <div className="space-y-3">
        {steps.map((step, index) => {
          const stepNum = index + 1;
          const isCurrentAction = actionLoadingKey === step.key;

          return (
            <div
              key={step.key}
              className="card p-4 flex items-center justify-between hover:bg-slate-50 transition"
            >
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-sm font-semibold text-blue-700">
                    {stepNum}
                  </span>
                  <div>
                    <h4 className="font-semibold text-slate-900">{step.title}</h4>
                    <p className="text-sm text-slate-600">{step.description}</p>
                  </div>
                </div>
              </div>

              <button
                type="button"
                onClick={() => onAction(step.key)}
                disabled={!currentRunId || isLoading}
                className="btn-primary ml-4 shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isCurrentAction ? "Working..." : step.buttonLabel}
              </button>
            </div>
          );
        })}
      </div>

      {!currentRunId && (
        <div className="mt-6 rounded-lg bg-amber-50 border border-amber-200 p-4 text-sm text-amber-800">
          Create or load a session first to run pipeline steps.
        </div>
      )}
    </SectionShell>
  );
}
