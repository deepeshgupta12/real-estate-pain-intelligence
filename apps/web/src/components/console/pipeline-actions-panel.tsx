"use client";

import { InfoTip } from "@/components/ui/info-tip";
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

const actionCards: Array<{
  key: PipelineActionKey;
  title: string;
  description: string;
  buttonLabel: string;
}> = [
  {
    key: "collect_feedback",
    title: "Start data collection",
    description:
      "Collect raw public feedback and create the first evidence records for the selected run.",
    buttonLabel: "Start data collection",
  },
  {
    key: "clean_text",
    title: "Clean text",
    description:
      "Clean and normalize the collected text so later stages use a more stable input.",
    buttonLabel: "Clean text",
  },
  {
    key: "prepare_language",
    title: "Prepare language support",
    description:
      "Resolve language and script details so multilingual feedback is easier to process.",
    buttonLabel: "Prepare language support",
  },
  {
    key: "generate_insights",
    title: "Generate insights",
    description:
      "Create structured pain-point insights, priority labels, and recommended actions.",
    buttonLabel: "Generate insights",
  },
  {
    key: "build_search_library",
    title: "Prepare search-ready knowledge",
    description:
      "Create the search-ready document layer so the run becomes easier to query later.",
    buttonLabel: "Prepare search-ready knowledge",
  },
  {
    key: "create_review_list",
    title: "Create review list",
    description:
      "Prepare the human review queue so a person can approve or reject generated insights.",
    buttonLabel: "Create review list",
  },
  {
    key: "prepare_notion_sync",
    title: "Prepare Notion sync",
    description:
      "Create sync jobs for approved review items. Approval must exist before this stage works.",
    buttonLabel: "Prepare Notion sync",
  },
  {
    key: "run_notion_sync",
    title: "Run Notion sync",
    description:
      "Try to send queued approved items into Notion using the already prepared sync jobs.",
    buttonLabel: "Run Notion sync",
  },
  {
    key: "create_exports",
    title: "Create downloadable files",
    description:
      "Generate CSV, JSON, and PDF outputs for the selected run.",
    buttonLabel: "Create files",
  },
  {
    key: "check_readiness",
    title: "Check final readiness",
    description:
      "Refresh the final readiness result for this run and confirm what is still missing.",
    buttonLabel: "Check final readiness",
  },
];

export function PipelineActionsPanel({
  currentRunId,
  actionLoadingKey,
  onAction,
}: PipelineActionsPanelProps) {
  return (
    <SectionShell
      id="pipeline-actions"
      eyebrow="Operate the workflow"
      title="Pipeline actions"
      description="Move the selected run stage by stage. Each action uses the backend APIs already available in the platform."
    >
      <div className="mb-5 rounded-3xl border border-white/10 bg-black/10 p-5">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold text-white">Simple action guide</h3>
          <InfoTip
            title="How to use these actions"
            description="You usually work from top to bottom. If a stage has not produced the required output yet, the backend will return a clear message."
          />
        </div>

        <div className="mt-4 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => onAction("refresh_workspace")}
            disabled={actionLoadingKey !== null}
            className="rounded-2xl border border-cyan-400/30 bg-cyan-400/10 px-5 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-400/15 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {actionLoadingKey === "refresh_workspace" ? "Refreshing..." : "Refresh workspace"}
          </button>

          {currentRunId ? (
            <span className="self-center text-sm text-white/60">
              Working on run #{currentRunId}
            </span>
          ) : (
            <span className="self-center text-sm text-amber-200">
              Create or load a run before using the actions below.
            </span>
          )}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {actionCards.map((action) => {
          const isLoading = actionLoadingKey === action.key;

          return (
            <div
              key={action.key}
              className="rounded-3xl border border-white/10 bg-black/10 p-5"
            >
              <h3 className="text-lg font-semibold text-white">{action.title}</h3>
              <p className="mt-3 text-sm leading-6 text-white/65">
                {action.description}
              </p>

              <div className="mt-4">
                <button
                  type="button"
                  onClick={() => onAction(action.key)}
                  disabled={!currentRunId || actionLoadingKey !== null}
                  className="rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isLoading ? "Working..." : action.buttonLabel}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </SectionShell>
  );
}