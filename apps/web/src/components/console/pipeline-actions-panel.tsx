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

const actionGroups: Array<{
  title: string;
  description: string;
  actions: Array<{
    key: PipelineActionKey;
    title: string;
    description: string;
    buttonLabel: string;
  }>;
}> = [
  {
    title: "Collection and preparation",
    description: "Create base evidence and stabilize raw inputs.",
    actions: [
      {
        key: "collect_feedback",
        title: "Start data collection",
        description:
          "Collect raw public feedback and create evidence for the selected run.",
        buttonLabel: "Start collection",
      },
      {
        key: "clean_text",
        title: "Clean text",
        description:
          "Normalize and clean the collected content before downstream analysis.",
        buttonLabel: "Clean text",
      },
      {
        key: "prepare_language",
        title: "Prepare language support",
        description:
          "Resolve multilingual and script signals for more reliable processing.",
        buttonLabel: "Prepare language",
      },
    ],
  },
  {
    title: "Analysis and indexing",
    description: "Generate structured output and make it query-ready.",
    actions: [
      {
        key: "generate_insights",
        title: "Generate insights",
        description:
          "Create pain points, priorities, recommended actions, and structured summaries.",
        buttonLabel: "Generate insights",
      },
      {
        key: "build_search_library",
        title: "Prepare search-ready knowledge",
        description:
          "Create retrieval documents so this run becomes searchable later.",
        buttonLabel: "Build search layer",
      },
      {
        key: "create_review_list",
        title: "Create review list",
        description:
          "Prepare moderation-ready review items for human validation.",
        buttonLabel: "Create review list",
      },
    ],
  },
  {
    title: "Sync and output",
    description: "Push approved output and create downloadable artifacts.",
    actions: [
      {
        key: "prepare_notion_sync",
        title: "Prepare Notion sync",
        description:
          "Create sync jobs for approved review items.",
        buttonLabel: "Prepare sync",
      },
      {
        key: "run_notion_sync",
        title: "Run Notion sync",
        description:
          "Attempt the actual sync using already prepared jobs.",
        buttonLabel: "Run sync",
      },
      {
        key: "create_exports",
        title: "Create downloadable files",
        description:
          "Generate CSV, JSON, and PDF output for the selected run.",
        buttonLabel: "Create files",
      },
      {
        key: "check_readiness",
        title: "Check final readiness",
        description:
          "Refresh readiness and confirm what is still missing.",
        buttonLabel: "Check readiness",
      },
    ],
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
      eyebrow="Run controls"
      title="Pipeline actions"
      description="Operate the active run from top to bottom. Actions are grouped by workflow purpose so the operating path is easier to understand."
    >
      <div className="workspace-soft mb-5 rounded-3xl p-5">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold text-white">Quick guidance</h3>
          <InfoTip
            title="How to use these actions"
            description="In most cases you will execute these in sequence. Backend guardrails will block stages whose prerequisites are still missing."
          />
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={() => onAction("refresh_workspace")}
            disabled={actionLoadingKey !== null}
            className="rounded-2xl border border-cyan-400/28 bg-cyan-400/12 px-5 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-400/18 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {actionLoadingKey === "refresh_workspace"
              ? "Refreshing..."
              : "Refresh workspace"}
          </button>

          {currentRunId ? (
            <span className="badge badge-info">Working on run #{currentRunId}</span>
          ) : (
            <span className="badge badge-warning">
              Create or load a run first
            </span>
          )}
        </div>
      </div>

      <div className="space-y-6">
        {actionGroups.map((group) => (
          <div key={group.title} className="workspace-soft rounded-3xl p-5">
            <div>
              <h3 className="text-lg font-semibold text-white">{group.title}</h3>
              <p className="mt-2 text-sm leading-6 text-white/58">
                {group.description}
              </p>
            </div>

            <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {group.actions.map((action) => {
                const isLoading = actionLoadingKey === action.key;

                return (
                  <div
                    key={action.key}
                    className="rounded-3xl border border-white/8 bg-white/[0.02] p-5"
                  >
                    <h4 className="text-base font-semibold text-white">
                      {action.title}
                    </h4>
                    <p className="mt-3 text-sm leading-6 text-white/62">
                      {action.description}
                    </p>

                    <div className="mt-4">
                      <button
                        type="button"
                        onClick={() => onAction(action.key)}
                        disabled={!currentRunId || actionLoadingKey !== null}
                        className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-semibold text-white transition hover:bg-white/9 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {isLoading ? "Working..." : action.buttonLabel}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </SectionShell>
  );
}