"use client";

import { useCallback, useMemo, useState } from "react";
import { Sidebar } from "@/components/app-shell/sidebar";
import { Topbar } from "@/components/app-shell/topbar";
import { HeroBanner } from "@/components/dashboard/hero-banner";
import { NavPreviewCard } from "@/components/dashboard/nav-preview-card";
import { OverviewStatCard } from "@/components/dashboard/overview-stat-card";
import { PipelineStageCard } from "@/components/dashboard/pipeline-stage-card";
import { CurrentRunPanel } from "@/components/console/current-run-panel";
import {
  PipelineActionsPanel,
  PipelineActionKey,
} from "@/components/console/pipeline-actions-panel";
import { PipelineProgressPanel } from "@/components/console/pipeline-progress-panel";
import { QueueHealthPanel } from "@/components/console/queue-health-panel";
import { ReviewConsolePanel } from "@/components/console/review-console-panel";
import { RunDiagnosticsPanel } from "@/components/console/run-diagnostics-panel";
import { RunEventsPanel } from "@/components/console/run-events-panel";
import { RunSetupPanel } from "@/components/console/run-setup-panel";
import {
  createScrapeRun,
  dispatchRun,
  executeNotionSyncJobsForRun,
  executeScrapeRun,
  fetchApiHealth,
  fetchApiMeta,
  fetchFinalHardeningOverview,
  fetchObservabilityOverview,
  fetchQueueHealth,
  fetchReviewQueue,
  fetchReviewSummary,
  fetchRunDiagnostics,
  fetchRunEvents,
  fetchRunReadiness,
  fetchScrapeRun,
  fetchScrapeRuns,
  fetchSupportedSources,
  generateExportJobs,
  generateHumanReviewQueue,
  generateNotionSyncJobs,
  indexRunRetrieval,
  normalizeRun,
  processMultilingualRun,
  processRunIntelligence,
  startRun,
  type FinalHardeningOverviewResponse,
  type ObservabilityOverviewResponse,
  type QueueHealthItem,
  type ReviewQueueItem,
  type ReviewSummaryResponse,
  type RunDiagnosticsResponse,
  type RunEventResponse,
  type RunReadinessResponse,
  type ScrapeRunCreatePayload,
  type ScrapeRunResponse,
} from "@/lib/api";
import { NavigationItem } from "@/types/navigation";

type WorkspaceShellProps = {
  initialApiStatus: string;
  initialApiSubtitle: string;
  initialApiVersion: string;
  initialEnvironment: string;
  initialAppName: string;
  initialApiPrefix: string;
  initialHardeningOverview: FinalHardeningOverviewResponse | null;
  initialObservabilityOverview: ObservabilityOverviewResponse | null;
  initialQueueHealth: QueueHealthItem[];
  initialRecentEvents: RunEventResponse[];
  initialReviewSummary: ReviewSummaryResponse;
  initialReviewQueue: ReviewQueueItem[];
  initialDiagnostics: RunDiagnosticsResponse | null;
  initialReadiness: RunReadinessResponse | null;
  initialRun: ScrapeRunResponse | null;
  initialRuns: ScrapeRunResponse[];
  initialSources: string[];
};

const navigationItems: NavigationItem[] = [
  {
    id: "overview",
    label: "Overview",
    description: "Platform health, key counts, and a quick snapshot of the workspace.",
    badge: "Live",
    active: true,
    href: "#overview",
  },
  {
    id: "run-workspace",
    label: "Run setup",
    description: "Create a new run or load an older one before operating the pipeline.",
    badge: "Action",
    href: "#run-workspace",
  },
  {
    id: "current-run",
    label: "Current run",
    description: "See the selected run, its status, counts, and current readiness.",
    badge: "Live",
    href: "#current-run",
  },
  {
    id: "pipeline-progress",
    label: "Pipeline progress",
    description: "Follow the run stage by stage with simple human-friendly labels.",
    badge: "Guide",
    href: "#pipeline-progress",
  },
  {
    id: "pipeline-actions",
    label: "Pipeline actions",
    description: "Run each stage directly from the frontend instead of only observing it.",
    badge: "Action",
    href: "#pipeline-actions",
  },
  {
    id: "queue-health",
    label: "Queue health",
    description: "Monitor active runs, latest events, and stale heartbeat warnings.",
    badge: "Live",
    href: "#queue-health",
  },
  {
    id: "run-diagnostics",
    label: "Run diagnostics",
    description: "Inspect a run in detail, including readiness and failure context.",
    badge: "Live",
    href: "#run-diagnostics",
  },
  {
    id: "run-events",
    label: "Run events",
    description: "Explore the event timeline with filters for stage, type, and status.",
    badge: "Live",
    href: "#run-events",
  },
  {
    id: "review-console",
    label: "Review console",
    description: "Validate generated insights using single and bulk moderation actions.",
    badge: "Live",
    href: "#review-console",
  },
];

export function WorkspaceShell({
  initialApiStatus,
  initialApiSubtitle,
  initialApiVersion,
  initialEnvironment,
  initialAppName,
  initialApiPrefix,
  initialHardeningOverview,
  initialObservabilityOverview,
  initialQueueHealth,
  initialRecentEvents,
  initialReviewSummary,
  initialReviewQueue,
  initialDiagnostics,
  initialReadiness,
  initialRun,
  initialRuns,
  initialSources,
}: WorkspaceShellProps) {
  const [apiStatus, setApiStatus] = useState(initialApiStatus);
  const [apiSubtitle, setApiSubtitle] = useState(initialApiSubtitle);
  const [apiVersion, setApiVersion] = useState(initialApiVersion);
  const [environment, setEnvironment] = useState(initialEnvironment);
  const [appName, setAppName] = useState(initialAppName);
  const [apiPrefix, setApiPrefix] = useState(initialApiPrefix);

  const [hardeningOverview, setHardeningOverview] = useState(
    initialHardeningOverview,
  );
  const [observabilityOverview, setObservabilityOverview] = useState(
    initialObservabilityOverview,
  );
  const [queueHealth, setQueueHealth] = useState(initialQueueHealth);
  const [recentEvents, setRecentEvents] = useState(initialRecentEvents);
  const [reviewSummary, setReviewSummary] = useState(initialReviewSummary);
  const [reviewQueue, setReviewQueue] = useState(initialReviewQueue);
  const [currentDiagnostics, setCurrentDiagnostics] = useState(initialDiagnostics);
  const [currentReadiness, setCurrentReadiness] = useState(initialReadiness);
  const [currentRun, setCurrentRun] = useState(initialRun);
  const [runs, setRuns] = useState(initialRuns);
  const [availableSources, setAvailableSources] = useState(initialSources);

  const [workspaceLoading, setWorkspaceLoading] = useState(false);
  const [actionLoadingKey, setActionLoadingKey] =
    useState<PipelineActionKey | null>(null);
  const [workspaceError, setWorkspaceError] = useState("");
  const [workspaceMessage, setWorkspaceMessage] = useState("");

  const activeQueueCount = observabilityOverview?.active_queue_count ?? 0;
  const staleRunsCount = observabilityOverview?.stale_active_runs_count ?? 0;
  const reviewBacklogCount = observabilityOverview?.review_backlog_count ?? 0;

  const currentRunId = currentRun?.id ?? null;

  const statusSummary = useMemo(() => {
    if (!currentRun) {
      return "No run selected yet.";
    }

    return `Run #${currentRun.id} is currently in "${currentRun.pipeline_stage.replaceAll(
      "_",
      " ",
    )}" with status "${currentRun.status}".`;
  }, [currentRun]);

  const refreshWorkspace = useCallback(
    async (preferredRunId?: number | null, successMessage?: string) => {
      setWorkspaceLoading(true);
      setWorkspaceError("");
      if (successMessage) {
        setWorkspaceMessage(successMessage);
      }

      try {
        const [
          health,
          meta,
          hardening,
          observability,
          queue,
          events,
          runsData,
          sourcesData,
        ] = await Promise.all([
          fetchApiHealth(),
          fetchApiMeta(),
          fetchFinalHardeningOverview(),
          fetchObservabilityOverview(),
          fetchQueueHealth(),
          fetchRunEvents({ limit: 20, newestFirst: true }),
          fetchScrapeRuns(),
          fetchSupportedSources(),
        ]);

        setApiStatus(health.status === "ok" ? "Connected" : health.status);
        setApiSubtitle(`${health.app_name} • ${health.environment}`);
        setApiVersion(meta.version);
        setEnvironment(meta.environment);
        setAppName(meta.app_name);
        setApiPrefix(meta.api_prefix);

        setHardeningOverview(hardening);
        setObservabilityOverview(observability);
        setQueueHealth(queue);
        setRecentEvents(events);
        setRuns(runsData);
        setAvailableSources(sourcesData);

        const nextRunId =
          preferredRunId ?? currentRun?.id ?? runsData[0]?.id ?? queue[0]?.run_id ?? null;

        if (nextRunId) {
          const [
            runData,
            diagnosticsData,
            readinessData,
            scopedSummary,
            scopedQueue,
          ] = await Promise.all([
            fetchScrapeRun(nextRunId),
            fetchRunDiagnostics(nextRunId),
            fetchRunReadiness(nextRunId),
            fetchReviewSummary(nextRunId),
            fetchReviewQueue({
              runId: nextRunId,
              includeDetails: true,
              limit: 20,
              offset: 0,
            }),
          ]);

          setCurrentRun(runData);
          setCurrentDiagnostics(diagnosticsData);
          setCurrentReadiness(readinessData);
          setReviewSummary(scopedSummary);
          setReviewQueue(scopedQueue);
        } else {
          const [globalSummary, globalQueue] = await Promise.all([
            fetchReviewSummary(),
            fetchReviewQueue({ includeDetails: true, limit: 20, offset: 0 }),
          ]);

          setCurrentRun(null);
          setCurrentDiagnostics(null);
          setCurrentReadiness(null);
          setReviewSummary(globalSummary);
          setReviewQueue(globalQueue);
        }
      } catch (error) {
        setWorkspaceError(
          error instanceof Error
            ? error.message
            : "Failed to refresh the workspace.",
        );
      } finally {
        setWorkspaceLoading(false);
      }
    },
    [currentRun],
  );

  async function handleCreateRun(payload: ScrapeRunCreatePayload) {
    setWorkspaceError("");
    setWorkspaceMessage("");
    setWorkspaceLoading(true);

    try {
      const createdRun = await createScrapeRun(payload);
      await refreshWorkspace(
        createdRun.id,
        `Run #${createdRun.id} created successfully.`,
      );
    } catch (error) {
      setWorkspaceError(
        error instanceof Error ? error.message : "Failed to create the run.",
      );
      setWorkspaceLoading(false);
    }
  }

  async function handleSelectRun(runId: number) {
    setWorkspaceError("");
    setWorkspaceMessage("");
    await refreshWorkspace(runId, `Loaded run #${runId}.`);
  }

  async function handleAction(action: PipelineActionKey) {
    if (action === "refresh_workspace") {
      await refreshWorkspace(currentRunId, "Workspace refreshed.");
      return;
    }

    if (!currentRunId) {
      setWorkspaceError("Create or load a run before using pipeline actions.");
      return;
    }

    setActionLoadingKey(action);
    setWorkspaceError("");
    setWorkspaceMessage("");

    try {
      if (action === "collect_feedback") {
        await executeScrapeRun(currentRunId);
        await refreshWorkspace(currentRunId, "Data collection completed.");
        return;
      }

      if (action === "clean_text") {
        await normalizeRun(currentRunId);
        await refreshWorkspace(currentRunId, "Text cleaning completed.");
        return;
      }

      if (action === "prepare_language") {
        await processMultilingualRun(currentRunId);
        await refreshWorkspace(currentRunId, "Language support step completed.");
        return;
      }

      if (action === "generate_insights") {
        await processRunIntelligence(currentRunId);
        await refreshWorkspace(currentRunId, "Insight generation completed.");
        return;
      }

      if (action === "build_search_library") {
        await indexRunRetrieval(currentRunId);
        await refreshWorkspace(currentRunId, "Search-ready knowledge prepared.");
        return;
      }

      if (action === "create_review_list") {
        await generateHumanReviewQueue(currentRunId);
        await refreshWorkspace(currentRunId, "Review list created successfully.");
        return;
      }

      if (action === "prepare_notion_sync") {
        await generateNotionSyncJobs(currentRunId);
        await refreshWorkspace(currentRunId, "Notion sync jobs prepared.");
        return;
      }

      if (action === "run_notion_sync") {
        await executeNotionSyncJobsForRun(currentRunId);
        await refreshWorkspace(currentRunId, "Notion sync run finished.");
        return;
      }

      if (action === "create_exports") {
        await generateExportJobs(currentRunId, {
          export_formats: ["csv", "json", "pdf"],
        });
        await refreshWorkspace(currentRunId, "Downloadable files created.");
        return;
      }

      if (action === "check_readiness") {
        await refreshWorkspace(currentRunId, "Final readiness refreshed.");
        return;
      }
    } catch (error) {
      setWorkspaceError(
        error instanceof Error ? error.message : "This pipeline action failed.",
      );
    } finally {
      setActionLoadingKey(null);
    }
  }

  async function handleQuickQueueAndStart() {
    if (!currentRunId) {
      setWorkspaceError("Create or load a run before using quick start.");
      return;
    }

    setActionLoadingKey("refresh_workspace");
    setWorkspaceError("");
    setWorkspaceMessage("");

    try {
      await dispatchRun(currentRunId);
      await startRun(currentRunId);
      await refreshWorkspace(currentRunId, "Run was queued and marked as started.");
    } catch (error) {
      setWorkspaceError(
        error instanceof Error ? error.message : "Failed to queue and start the run.",
      );
    } finally {
      setActionLoadingKey(null);
    }
  }

  return (
    <main className="min-h-screen xl:flex">
      <Sidebar items={navigationItems} />

      <div className="min-w-0 flex-1">
        <Topbar
          environment={environment}
          version={apiVersion}
          apiStatus={apiStatus}
        />

        <div className="mx-auto max-w-7xl px-5 py-6 lg:px-8 lg:py-8">
          <div id="overview">
            <HeroBanner
              apiStatus={apiStatus}
              apiSubtitle={apiSubtitle}
              activeQueueCount={activeQueueCount}
              staleRunsCount={staleRunsCount}
              backlogCount={reviewBacklogCount}
            />
          </div>

          <section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <OverviewStatCard
              label="Application"
              value={appName}
              helper="Frontend workspace now supports both operating the run and monitoring it."
            />
            <OverviewStatCard
              label="Environment"
              value={environment}
              helper="Pulled from backend settings and shown across the workspace."
            />
            <OverviewStatCard
              label="API Prefix"
              value={apiPrefix}
              helper="The route base used for run actions, review flows, and monitoring."
            />
            <OverviewStatCard
              label="Current Build Step"
              value="Step 26B"
              helper="Run-scoped review workspace and clearer operational visibility."
            />
          </section>

          <section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <OverviewStatCard
              label="Total Runs"
              value={hardeningOverview?.runs_total ?? 0}
              helper="All runs created so far."
            />
            <OverviewStatCard
              label="Completed Runs"
              value={hardeningOverview?.runs_completed ?? 0}
              helper="Runs that finished successfully."
            />
            <OverviewStatCard
              label="Failed Runs"
              value={hardeningOverview?.runs_failed ?? 0}
              helper="Runs that need attention."
            />
            <OverviewStatCard
              label="Run Events"
              value={hardeningOverview?.run_events_total ?? 0}
              helper="Operational event volume across the platform."
            />
          </section>

          <section className="mt-8 grid gap-6 xl:grid-cols-2">
            <NavPreviewCard
              title="What changes in Step 26B"
              description="The workspace is now more reliable for run-specific review operations and signal inspection."
              points={[
                "Review console defaults to the active run instead of mixed global data",
                "Run-level review summary stays aligned with the selected run",
                "Analysis mode and live versus stub evidence are easier to inspect",
                "Current run snapshot now surfaces signal quality from review outputs",
              ]}
            />

            <NavPreviewCard
              title="Quick context"
              description={statusSummary}
              points={[
                workspaceLoading ? "Workspace refresh is in progress" : "Workspace is ready",
                currentReadiness?.ready_for_finalization
                  ? "The current run passes final readiness"
                  : "The current run still has pending readiness checks",
                `Available feedback sources: ${availableSources.length}`,
                `Saved runs visible in workspace: ${runs.length}`,
              ]}
            />
          </section>

          <section className="mt-8">
            <div className="mb-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/45">
                Product pipeline coverage
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-white">
                Actionable stage flow
              </h2>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-white/60">
                These cards translate the backend pipeline into simple language
                so the flow is easier to understand while still mapping to the
                real system actions.
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <PipelineStageCard
                step="Stage 01"
                title="Collect feedback"
                description="Create the run and bring public comments or reviews into the system."
              />
              <PipelineStageCard
                step="Stage 02"
                title="Prepare the text"
                description="Clean the content and prepare language handling before analysis."
              />
              <PipelineStageCard
                step="Stage 03"
                title="Create insights"
                description="Generate pain points, priorities, review items, and search-ready knowledge."
              />
              <PipelineStageCard
                step="Stage 04"
                title="Use the output"
                description="Sync approved items, create files, and confirm final readiness."
              />
            </div>
          </section>

          <div className="mt-8 space-y-4">
            {(workspaceMessage || workspaceError) && (
              <div
                className={`rounded-3xl border px-4 py-4 text-sm ${
                  workspaceError
                    ? "border-red-400/20 bg-red-400/10 text-red-100"
                    : "border-emerald-400/20 bg-emerald-400/10 text-emerald-100"
                }`}
              >
                {workspaceError || workspaceMessage}
              </div>
            )}

            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={handleQuickQueueAndStart}
                disabled={
                  !currentRunId || actionLoadingKey !== null || workspaceLoading
                }
                className="rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Quick queue + start
              </button>

              <button
                type="button"
                onClick={() =>
                  refreshWorkspace(currentRunId, "Workspace refreshed.")
                }
                disabled={workspaceLoading || actionLoadingKey !== null}
                className="rounded-2xl border border-cyan-400/30 bg-cyan-400/10 px-5 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-400/15 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {workspaceLoading ? "Refreshing..." : "Refresh everything"}
              </button>
            </div>
          </div>

          <div className="mt-8 space-y-8">
            <RunSetupPanel
              availableSources={availableSources}
              runs={runs}
              currentRunId={currentRunId}
              loading={workspaceLoading}
              onCreateRun={handleCreateRun}
              onSelectRun={handleSelectRun}
            />

            <CurrentRunPanel
              currentRun={currentRun}
              readiness={currentReadiness}
              reviewQueue={reviewQueue}
            />

            <PipelineProgressPanel
              currentRun={currentRun}
              readiness={currentReadiness}
            />

            <PipelineActionsPanel
              currentRunId={currentRunId}
              actionLoadingKey={actionLoadingKey}
              onAction={handleAction}
            />

            <QueueHealthPanel queueItems={queueHealth} />

            <RunDiagnosticsPanel
              initialRunId={currentRunId}
              initialDiagnostics={currentDiagnostics}
            />

            <RunEventsPanel initialEvents={recentEvents} />

            <ReviewConsolePanel
              initialRunId={currentRunId}
              activeRunId={currentRunId}
              initialSummary={reviewSummary}
              initialQueue={reviewQueue}
            />
          </div>
        </div>
      </div>
    </main>
  );
}