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
    description: "Workspace summary and current operating context.",
    badge: "Live",
    active: true,
    href: "#overview",
  },
  {
    id: "run-workspace",
    label: "Run setup",
    description: "Create a run or switch to an existing run.",
    badge: "Action",
    href: "#run-workspace",
  },
  {
    id: "current-run",
    label: "Current run",
    description: "Active run identity, readiness, and signal quality.",
    badge: "Live",
    href: "#current-run",
  },
  {
    id: "pipeline-progress",
    label: "Pipeline progress",
    description: "Readable stage-level progress for the active run.",
    badge: "Guide",
    href: "#pipeline-progress",
  },
  {
    id: "pipeline-actions",
    label: "Pipeline actions",
    description: "Execute pipeline steps from the workspace.",
    badge: "Action",
    href: "#pipeline-actions",
  },
  {
    id: "queue-health",
    label: "Queue health",
    description: "Queue freshness, health labels, and recent signals.",
    badge: "Live",
    href: "#queue-health",
  },
  {
    id: "run-diagnostics",
    label: "Run diagnostics",
    description: "Deep inspection for one run at a time.",
    badge: "Live",
    href: "#run-diagnostics",
  },
  {
    id: "run-events",
    label: "Run events",
    description: "Explore filtered operational events.",
    badge: "Live",
    href: "#run-events",
  },
  {
    id: "review-console",
    label: "Review console",
    description: "Moderate, inspect, and bulk-handle review items.",
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
      return "No run is selected. Create a new run or load an existing run to begin operating the workspace.";
    }

    return `Run #${currentRun.id} is active for ${currentRun.target_brand} and is currently in "${currentRun.pipeline_stage.replaceAll(
      "_",
      " ",
    )}" with status "${currentRun.status.replaceAll("_", " ")}".`;
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
              helper="Frontend workspace supports both operation and monitoring."
            />
            <OverviewStatCard
              label="Environment"
              value={environment}
              helper="Pulled directly from backend meta settings."
            />
            <OverviewStatCard
              label="API Prefix"
              value={apiPrefix}
              helper="Base route used across run actions and monitoring calls."
            />
            <OverviewStatCard
              label="Current build"
              value="Step 26B"
              helper="Workspace UX reset and review moderation redesign."
            />
          </section>

          <section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <OverviewStatCard
              label="Total runs"
              value={hardeningOverview?.runs_total ?? 0}
              helper="All created runs visible to the workspace."
            />
            <OverviewStatCard
              label="Completed runs"
              value={hardeningOverview?.runs_completed ?? 0}
              helper="Runs that finished successfully."
            />
            <OverviewStatCard
              label="Failed runs"
              value={hardeningOverview?.runs_failed ?? 0}
              helper="Runs that still need attention."
            />
            <OverviewStatCard
              label="Run events"
              value={hardeningOverview?.run_events_total ?? 0}
              helper="Total operational event volume tracked in the system."
            />
          </section>

          <section className="mt-8 grid gap-6 xl:grid-cols-2">
            <NavPreviewCard
              title="What this redesign improves"
              description="This step focuses on layout clarity and operator ease, not on adding more UI noise."
              points={[
                "Cleaner run-first operating flow",
                "Monitoring sections feel lighter and easier to scan",
                "Review moderation is now more structured and less table-heavy",
                "Current workspace state is easier to understand at a glance",
              ]}
            />

            <NavPreviewCard
              title="Current workspace context"
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
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/38">
                Pipeline flow
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-white">
                Operating path
              </h2>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-white/58">
                These cards translate the backend pipeline into a smaller set of
                understandable product steps before the detailed stage tracker below.
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <PipelineStageCard
                step="Stage 01"
                title="Collect feedback"
                description="Create or load a run and bring public feedback into the system."
              />
              <PipelineStageCard
                step="Stage 02"
                title="Prepare inputs"
                description="Clean and normalize the evidence for downstream analysis."
              />
              <PipelineStageCard
                step="Stage 03"
                title="Generate output"
                description="Create insights, review items, and retrieval-ready documents."
              />
              <PipelineStageCard
                step="Stage 04"
                title="Use the output"
                description="Sync approved items, export files, and confirm readiness."
              />
            </div>
          </section>

          <div className="mt-8 space-y-4">
            {(workspaceMessage || workspaceError) && (
              <div
                className={`rounded-3xl border px-4 py-4 text-sm ${
                  workspaceError
                    ? "border-red-400/18 bg-red-400/10 text-red-100"
                    : "border-emerald-400/18 bg-emerald-400/10 text-emerald-100"
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
                className="rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/8 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Quick queue + start
              </button>

              <button
                type="button"
                onClick={() =>
                  refreshWorkspace(currentRunId, "Workspace refreshed.")
                }
                disabled={workspaceLoading || actionLoadingKey !== null}
                className="rounded-2xl border border-cyan-400/28 bg-cyan-400/12 px-5 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-400/18 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {workspaceLoading ? "Refreshing..." : "Refresh everything"}
              </button>

              {currentRunId ? (
                <span className="badge badge-info self-center">
                  Active run #{currentRunId}
                </span>
              ) : (
                <span className="badge badge-warning self-center">
                  No active run selected
                </span>
              )}
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