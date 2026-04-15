"use client";

import { useCallback, useEffect, useState } from "react";
import { Sidebar } from "@/components/app-shell/sidebar";
import { Topbar } from "@/components/app-shell/topbar";
import { HeroBanner } from "@/components/dashboard/hero-banner";
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
import { ExportsPanel } from "@/components/console/exports-panel";
import { PainPointsPanel } from "@/components/console/pain-points-panel";
import { EvidenceExplorerPanel } from "@/components/console/evidence-explorer-panel";
import { RetrievalSearchPanel } from "@/components/console/retrieval-search-panel";
import { ErrorBoundary } from "@/components/ui/error-boundary";
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
  fetchScrapeRunItems,
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
    label: "Dashboard",
    description: "System overview and quick stats.",
    badge: "Live",
    active: true,
    href: "#overview",
  },
  {
    id: "run-workspace",
    label: "New Session",
    description: "Start a new research session or load an existing one.",
    badge: "Action",
    href: "#run-workspace",
  },
  {
    id: "current-run",
    label: "Current Session",
    description: "View the active session status and readiness.",
    badge: "Live",
    href: "#current-run",
  },
  {
    id: "pipeline-progress",
    label: "Step Progress",
    description: "Track which steps have completed.",
    badge: "Guide",
    href: "#pipeline-progress",
  },
  {
    id: "pain-points",
    label: "Pain Points",
    description: "Pain point insights grouped by buyer persona.",
    badge: "Live",
    href: "#pain-points",
  },
  {
    id: "pipeline-actions",
    label: "Run Steps",
    description: "Execute each step of the research pipeline.",
    badge: "Action",
    href: "#pipeline-actions",
  },
  {
    id: "queue-health",
    label: "Active Sessions",
    description: "See all running research sessions.",
    badge: "Live",
    href: "#queue-health",
  },
  {
    id: "run-diagnostics",
    label: "Session Details",
    description: "Deep-inspect any session by ID.",
    badge: "Live",
    href: "#run-diagnostics",
  },
  {
    id: "run-events",
    label: "Activity Log",
    description: "Full timeline of events for this session.",
    badge: "Live",
    href: "#run-events",
  },
  {
    id: "evidence-explorer",
    label: "Evidence Explorer",
    description: "Browse all raw posts, reviews, and comments collected.",
    badge: "Live",
    href: "#evidence-explorer",
  },
  {
    id: "retrieval-search",
    label: "Semantic Search",
    description: "Search the indexed knowledge base with natural language.",
    badge: "Search",
    href: "#retrieval-search",
  },
  {
    id: "review-console",
    label: "Review Queue",
    description: "Approve or reject identified pain points.",
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
  const [exportRefreshKey, setExportRefreshKey] = useState(0);
  const [insightRefreshKey, setInsightRefreshKey] = useState(0);

  // Scroll to top on mount so page refresh doesn't restore a mid-page hash position
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
  }, []);

  const activeQueueCount = observabilityOverview?.active_queue_count ?? 0;
  const staleRunsCount = observabilityOverview?.stale_active_runs_count ?? 0;
  const reviewBacklogCount = observabilityOverview?.review_backlog_count ?? 0;
  const currentRunId = currentRun?.id ?? null;

  const refreshWorkspace = useCallback(
    async (preferredRunId?: number | null, successMessage?: string) => {
      setWorkspaceLoading(true);
      setWorkspaceError("");
      if (successMessage) {
        setWorkspaceMessage(successMessage);
      }

      // Use allSettled so a single failing endpoint (e.g. a missing DB column during
      // a migration gap) cannot wipe out the entire UI initialisation.  Each call
      // that succeeds still populates its state; only the failing ones are skipped.
      try {
        const [
          healthResult,
          metaResult,
          hardeningResult,
          observabilityResult,
          queueResult,
          eventsResult,
          runsResult,
          sourcesResult,
        ] = await Promise.allSettled([
          fetchApiHealth(),
          fetchApiMeta(),
          fetchFinalHardeningOverview(),
          fetchObservabilityOverview(),
          fetchQueueHealth(),
          fetchRunEvents({ limit: 20, newestFirst: true }),
          fetchScrapeRunItems(),
          fetchSupportedSources(),
        ]);

        // Collect non-critical errors for display
        const errors: string[] = [];
        const settled = <T,>(r: PromiseSettledResult<T>, label: string): T | undefined => {
          if (r.status === "fulfilled") return r.value;
          errors.push(`${label}: ${r.reason instanceof Error ? r.reason.message : String(r.reason)}`);
          return undefined;
        };

        const health = settled(healthResult, "health");
        const meta = settled(metaResult, "meta");
        const hardening = settled(hardeningResult, "hardening");
        const observability = settled(observabilityResult, "observability");
        const queue = settled(queueResult, "queue");
        const events = settled(eventsResult, "events");
        const runsData = settled(runsResult, "runs");
        const sourcesData = settled(sourcesResult, "sources");

        if (health) {
          setApiStatus(health.status === "ok" ? "Connected" : health.status);
          setApiSubtitle(`${health.app_name} • ${health.environment}`);
        }
        if (meta) {
          setApiVersion(meta.version);
          setEnvironment(meta.environment);
          setAppName(meta.app_name);
          setApiPrefix(meta.api_prefix);
        }
        if (hardening) setHardeningOverview(hardening);
        if (observability) setObservabilityOverview(observability);
        if (queue) setQueueHealth(queue);
        if (events) setRecentEvents(events);
        if (runsData) setRuns(runsData);
        if (sourcesData && sourcesData.length > 0) setAvailableSources(sourcesData);

        // Show a summarised error only if the core health check itself failed
        if (errors.length > 0 && !health) {
          setWorkspaceError(errors[0]);
        } else if (errors.length > 0) {
          // Non-fatal: log to console only, don't break the UI
          console.warn("Some workspace endpoints returned errors:", errors);
        }

        const safeQueue = queueResult.status === "fulfilled" ? queueResult.value : [];
        const safeRuns = runsData ?? [];
        const nextRunId =
          preferredRunId ?? currentRun?.id ?? safeRuns[0]?.id ?? safeQueue[0]?.run_id ?? null;

        if (nextRunId) {
          const [
            runData,
            diagnosticsData,
            readinessData,
            scopedSummary,
            scopedQueue,
          ] = await Promise.allSettled([
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

          if (runData.status === "fulfilled") setCurrentRun(runData.value);
          if (diagnosticsData.status === "fulfilled") setCurrentDiagnostics(diagnosticsData.value);
          if (readinessData.status === "fulfilled") setCurrentReadiness(readinessData.value);
          if (scopedSummary.status === "fulfilled") setReviewSummary(scopedSummary.value);
          if (scopedQueue.status === "fulfilled") setReviewQueue(scopedQueue.value);
        } else {
          const [globalSummary, globalQueue] = await Promise.allSettled([
            fetchReviewSummary(),
            fetchReviewQueue({ includeDetails: true, limit: 20, offset: 0 }),
          ]);

          setCurrentRun(null);
          setCurrentDiagnostics(null);
          setCurrentReadiness(null);
          if (globalSummary.status === "fulfilled") setReviewSummary(globalSummary.value);
          if (globalQueue.status === "fulfilled") setReviewQueue(globalQueue.value);
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
        setInsightRefreshKey((k) => k + 1);
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
        setExportRefreshKey((k) => k + 1);
        await refreshWorkspace(currentRunId, "Downloadable files created. See the Exports panel below.");
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

          <section className="mt-8">
            <div className="mb-4">
              <p className="text-[11px] font-semibold uppercase tracking-widest text-blue-600">
                Research Pipeline
              </p>
              <h2 className="mt-1 text-xl font-semibold tracking-tight text-slate-900">
                How it works
              </h2>
              <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-500">
                Four stages take you from raw customer posts to actionable pain point reports.
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
                className={`rounded-lg border px-4 py-3 text-sm font-medium ${
                  workspaceError
                    ? "border-red-200 bg-red-50 text-red-700"
                    : "border-green-200 bg-green-50 text-green-700"
                }`}
              >
                {workspaceError || workspaceMessage}
              </div>
            )}

            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={handleQuickQueueAndStart}
                disabled={
                  !currentRunId || actionLoadingKey !== null || workspaceLoading
                }
                className="rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                ▶ Quick Start Session
              </button>

              <button
                type="button"
                onClick={() =>
                  refreshWorkspace(currentRunId, "Workspace refreshed.")
                }
                disabled={workspaceLoading || actionLoadingKey !== null}
                className="rounded-lg border border-blue-300 bg-blue-50 px-5 py-2.5 text-sm font-semibold text-blue-700 shadow-sm transition hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {workspaceLoading ? "Refreshing…" : "↻ Refresh"}
              </button>

              {currentRunId ? (
                <span className="inline-flex items-center gap-1.5 rounded-full border border-green-200 bg-green-50 px-3 py-1 text-xs font-semibold text-green-700">
                  <span className="h-1.5 w-1.5 rounded-full bg-green-500"></span>
                  Active Session #{currentRunId}
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">
                  <span className="h-1.5 w-1.5 rounded-full bg-amber-400"></span>
                  No session selected
                </span>
              )}
            </div>
          </div>

          <div className="mt-8 space-y-8">
            <ErrorBoundary label="New Session">
              <RunSetupPanel
                availableSources={availableSources}
                runs={runs}
                currentRunId={currentRunId}
                loading={workspaceLoading}
                onCreateRun={handleCreateRun}
                onSelectRun={handleSelectRun}
              />
            </ErrorBoundary>

            <ErrorBoundary label="Current Session">
              <CurrentRunPanel
                currentRun={currentRun}
                readiness={currentReadiness}
                reviewQueue={reviewQueue}
              />
            </ErrorBoundary>

            <ErrorBoundary label="Step Progress">
              <PipelineProgressPanel
                currentRun={currentRun}
                readiness={currentReadiness}
              />
            </ErrorBoundary>

            <ErrorBoundary label="Pain Points">
              <PainPointsPanel runId={currentRunId} insightRefreshKey={insightRefreshKey} />
            </ErrorBoundary>

            <ErrorBoundary label="Run Steps">
              <PipelineActionsPanel
                currentRunId={currentRunId}
                actionLoadingKey={actionLoadingKey}
                onAction={handleAction}
                lastActionError={workspaceError || undefined}
              />
            </ErrorBoundary>

            <ErrorBoundary label="Exports">
              <ExportsPanel runId={currentRunId} triggerRefresh={exportRefreshKey} />
            </ErrorBoundary>

            <ErrorBoundary label="Evidence Explorer">
              <EvidenceExplorerPanel runId={currentRunId} />
            </ErrorBoundary>

            <ErrorBoundary label="Retrieval Search">
              <RetrievalSearchPanel runId={currentRunId} />
            </ErrorBoundary>

            <ErrorBoundary label="Active Sessions">
              <QueueHealthPanel queueItems={queueHealth} />
            </ErrorBoundary>

            <ErrorBoundary label="Session Details">
              <RunDiagnosticsPanel
                initialRunId={currentRunId}
                initialDiagnostics={currentDiagnostics}
              />
            </ErrorBoundary>

            <ErrorBoundary label="Activity Log">
              <RunEventsPanel initialEvents={recentEvents} />
            </ErrorBoundary>

            <ErrorBoundary label="Review Queue">
              <ReviewConsolePanel
                initialRunId={currentRunId}
                activeRunId={currentRunId}
                initialSummary={reviewSummary}
                initialQueue={reviewQueue}
              />
            </ErrorBoundary>
          </div>
        </div>
      </div>
    </main>
  );
}