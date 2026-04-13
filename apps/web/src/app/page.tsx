import { WorkspaceShell } from "@/components/console/workspace-shell";
import {
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
  type FinalHardeningOverviewResponse,
  type ObservabilityOverviewResponse,
  type QueueHealthItem,
  type ReviewQueueItem,
  type ReviewSummaryResponse,
  type RunDiagnosticsResponse,
  type RunEventResponse,
  type RunReadinessResponse,
  type ScrapeRunResponse,
} from "@/lib/api";

export default async function Home() {
  let apiStatus = "Unavailable";
  let apiSubtitle = "Backend not reachable";
  let apiVersion = "Unknown";
  let environment = "unknown";
  let appName = "Market Intelligence";
  let apiPrefix = "/api/v1";

  let hardeningOverview: FinalHardeningOverviewResponse | null = null;
  let observabilityOverview: ObservabilityOverviewResponse | null = null;
  let queueHealth: QueueHealthItem[] = [];
  let recentEvents: RunEventResponse[] = [];
  let reviewSummary: ReviewSummaryResponse | null = null;
  let reviewQueue: ReviewQueueItem[] = [];
  let initialDiagnostics: RunDiagnosticsResponse | null = null;
  let initialReadiness: RunReadinessResponse | null = null;
  let initialRun: ScrapeRunResponse | null = null;
  let initialRuns: ScrapeRunResponse[] = [];
  let initialSources: string[] = [];

  try {
    const [
      health,
      meta,
      hardening,
      observability,
      queue,
      events,
      runs,
      sources,
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

    apiStatus = health.status === "ok" ? "Connected" : health.status;
    apiSubtitle = `${health.app_name} • ${health.environment}`;
    apiVersion = meta.version;
    environment = meta.environment;
    appName = meta.app_name;
    apiPrefix = meta.api_prefix;

    hardeningOverview = hardening;
    observabilityOverview = observability;
    queueHealth = queue;
    recentEvents = events;
    initialRuns = runs;
    initialSources = sources;

    const preferredRunId = runs[0]?.id ?? queue[0]?.run_id ?? null;

    if (preferredRunId) {
      const [run, diagnostics, readiness, scopedSummary, scopedReviews] =
        await Promise.all([
          fetchScrapeRun(preferredRunId),
          fetchRunDiagnostics(preferredRunId),
          fetchRunReadiness(preferredRunId),
          fetchReviewSummary(preferredRunId),
          fetchReviewQueue({
            runId: preferredRunId,
            includeDetails: true,
            limit: 20,
            offset: 0,
          }),
        ]);

      initialRun = run;
      initialDiagnostics = diagnostics;
      initialReadiness = readiness;
      reviewSummary = scopedSummary;
      reviewQueue = scopedReviews;
    } else {
      const [globalSummary, globalReviews] = await Promise.all([
        fetchReviewSummary(),
        fetchReviewQueue({ includeDetails: true, limit: 20, offset: 0 }),
      ]);

      reviewSummary = globalSummary;
      reviewQueue = globalReviews;
    }
  } catch {
    apiStatus = "Unavailable";
    apiSubtitle = "Start the FastAPI service on port 8000";
    apiVersion = "N/A";
    environment = "offline";
  }

  return (
    <WorkspaceShell
      initialApiStatus={apiStatus}
      initialApiSubtitle={apiSubtitle}
      initialApiVersion={apiVersion}
      initialEnvironment={environment}
      initialAppName={appName}
      initialApiPrefix={apiPrefix}
      initialHardeningOverview={hardeningOverview}
      initialObservabilityOverview={observabilityOverview}
      initialQueueHealth={queueHealth}
      initialRecentEvents={recentEvents}
      initialReviewSummary={
        reviewSummary ?? {
          run_id: null,
          total_items: 0,
          pending_review_count: 0,
          reviewed_count: 0,
          approved_count: 0,
          rejected_count: 0,
          high_priority_count: 0,
          llm_assisted_count: 0,
          deterministic_count: 0,
        }
      }
      initialReviewQueue={reviewQueue}
      initialDiagnostics={initialDiagnostics}
      initialReadiness={initialReadiness}
      initialRun={initialRun}
      initialRuns={initialRuns}
      initialSources={initialSources}
    />
  );
}