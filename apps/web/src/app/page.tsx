import { Sidebar } from "@/components/app-shell/sidebar";
import { Topbar } from "@/components/app-shell/topbar";
import { HeroBanner } from "@/components/dashboard/hero-banner";
import { NavPreviewCard } from "@/components/dashboard/nav-preview-card";
import { OverviewStatCard } from "@/components/dashboard/overview-stat-card";
import { PipelineStageCard } from "@/components/dashboard/pipeline-stage-card";
import { QueueHealthPanel } from "@/components/console/queue-health-panel";
import { ReviewConsolePanel } from "@/components/console/review-console-panel";
import { RunDiagnosticsPanel } from "@/components/console/run-diagnostics-panel";
import { RunEventsPanel } from "@/components/console/run-events-panel";
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
  type FinalHardeningOverviewResponse,
  type ObservabilityOverviewResponse,
  type QueueHealthItem,
  type ReviewQueueItem,
  type ReviewSummaryResponse,
  type RunDiagnosticsResponse,
  type RunEventResponse,
} from "@/lib/api";
import { NavigationItem } from "@/types/navigation";

const navigationItems: NavigationItem[] = [
  {
    id: "overview",
    label: "Overview Dashboard",
    description: "Live product-health snapshot, system metrics, and operational entry point.",
    badge: "Live",
    active: true,
    href: "#overview",
  },
  {
    id: "queue-health",
    label: "Queue Health",
    description: "Observe active runs, stale heartbeat detection, and latest event activity.",
    badge: "Live",
    href: "#queue-health",
  },
  {
    id: "run-diagnostics",
    label: "Run Diagnostics",
    description: "Inspect latest event, readiness state, stage timeline, and failure context.",
    badge: "Live",
    href: "#run-diagnostics",
  },
  {
    id: "run-events",
    label: "Run Events",
    description: "Explore operational events by run, stage, type, status, and ordering.",
    badge: "Live",
    href: "#run-events",
  },
  {
    id: "review-console",
    label: "Review Console",
    description: "Review queue summary, detail inspection, and moderation actions.",
    badge: "Live",
    href: "#review-console",
  },
];

export default async function Home() {
  let apiStatus = "Unavailable";
  let apiSubtitle = "Backend not reachable";
  let apiVersion = "Unknown";
  let environment = "unknown";
  let appName = "Pain Intelligence";
  let apiPrefix = "/api/v1";

  let hardeningOverview: FinalHardeningOverviewResponse | null = null;
  let observabilityOverview: ObservabilityOverviewResponse | null = null;
  let queueHealth: QueueHealthItem[] = [];
  let recentEvents: RunEventResponse[] = [];
  let reviewSummary: ReviewSummaryResponse | null = null;
  let reviewQueue: ReviewQueueItem[] = [];
  let initialDiagnostics: RunDiagnosticsResponse | null = null;

  try {
    const [
      health,
      meta,
      hardening,
      observability,
      queue,
      events,
      summary,
      reviews,
    ] = await Promise.all([
      fetchApiHealth(),
      fetchApiMeta(),
      fetchFinalHardeningOverview(),
      fetchObservabilityOverview(),
      fetchQueueHealth(),
      fetchRunEvents({ limit: 20, newestFirst: true }),
      fetchReviewSummary(),
      fetchReviewQueue({ includeDetails: true, limit: 20, offset: 0 }),
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
    reviewSummary = summary;
    reviewQueue = reviews;

    if (queue.length > 0) {
      initialDiagnostics = await fetchRunDiagnostics(queue[0].run_id);
    }
  } catch {
    apiStatus = "Unavailable";
    apiSubtitle = "Start the FastAPI service on port 8000";
    apiVersion = "N/A";
    environment = "offline";
  }

  const activeQueueCount = observabilityOverview?.active_queue_count ?? 0;
  const staleRunsCount = observabilityOverview?.stale_active_runs_count ?? 0;
  const reviewBacklogCount = observabilityOverview?.review_backlog_count ?? 0;

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
              helper="Frontend console wired to live backend metadata and operational endpoints."
            />
            <OverviewStatCard
              label="Environment"
              value={environment}
              helper="Pulled from backend settings and surfaced across the console."
            />
            <OverviewStatCard
              label="API Prefix"
              value={apiPrefix}
              helper="Versioned route base used for diagnostics, review, and observability."
            />
            <OverviewStatCard
              label="Current Build Step"
              value="Step 25"
              helper="Full frontend product console implementation."
            />
          </section>

          <section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <OverviewStatCard
              label="Total Runs"
              value={hardeningOverview?.runs_total ?? 0}
              helper="All scrape runs created in the system so far."
            />
            <OverviewStatCard
              label="Completed Runs"
              value={hardeningOverview?.runs_completed ?? 0}
              helper="Runs that reached the completed lifecycle state."
            />
            <OverviewStatCard
              label="Failed Runs"
              value={hardeningOverview?.runs_failed ?? 0}
              helper="Runs that entered failed state and require inspection."
            />
            <OverviewStatCard
              label="Run Events"
              value={hardeningOverview?.run_events_total ?? 0}
              helper="Persisted operational event timeline volume across the platform."
            />
          </section>

          <section className="mt-8 grid gap-6 xl:grid-cols-2">
            <NavPreviewCard
              title="Live operational coverage"
              description="The frontend now surfaces the most important backend capabilities already implemented through earlier steps."
              points={[
                "System overview, observability overview, and queue-health visibility",
                "Run diagnostics with readiness and failure state snapshots",
                "Run-event explorer with backend-driven filtering",
                "Human review summary, joined queue detail, and moderation actions",
              ]}
            />

            <NavPreviewCard
              title="What Step 25 unlocks"
              description="The console has moved beyond a static shell and now acts as an operational workspace for product intelligence workflows."
              points={[
                "Inspect stale active runs and latest event activity quickly",
                "Drill into a run’s stage-by-stage progression",
                "Moderate agent-generated insights using single and bulk actions",
                "Track backlog and observability metrics without leaving the frontend",
              ]}
            />
          </section>

          <section className="mt-8">
            <div className="mb-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/45">
                Product pipeline coverage
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-white">
                Backend-to-frontend operational chain
              </h2>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-white/60">
                The frontend console is now aligned to the main pipeline surfaces
                built in the backend through Steps 1–24.
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <PipelineStageCard
                step="Stage 01"
                title="Ingestion and evidence"
                description="Public-source collection, raw evidence storage, cleaning, normalization, and multilingual handling."
              />
              <PipelineStageCard
                step="Stage 02"
                title="Intelligence and retrieval"
                description="Hybrid intelligence, embedding retrieval, and structured issue understanding."
              />
              <PipelineStageCard
                step="Stage 03"
                title="Review and decisioning"
                description="Human review console readiness, approval workflows, and action moderation."
              />
              <PipelineStageCard
                step="Stage 04"
                title="Observability and export"
                description="Run diagnostics, queue observability, Notion sync, exports, and readiness monitoring."
              />
            </div>
          </section>

          <div className="mt-8 space-y-8">
            <QueueHealthPanel queueItems={queueHealth} />

            <RunDiagnosticsPanel
              initialRunId={queueHealth[0]?.run_id ?? null}
              initialDiagnostics={initialDiagnostics}
            />

            <RunEventsPanel initialEvents={recentEvents} />

            <ReviewConsolePanel
              initialSummary={
                reviewSummary ?? {
                  run_id: 0,
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
              initialQueue={reviewQueue}
            />
          </div>
        </div>
      </div>
    </main>
  );
}