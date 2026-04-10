import { Sidebar } from "@/components/app-shell/sidebar";
import { Topbar } from "@/components/app-shell/topbar";
import { HeroBanner } from "@/components/dashboard/hero-banner";
import { NavPreviewCard } from "@/components/dashboard/nav-preview-card";
import { OverviewStatCard } from "@/components/dashboard/overview-stat-card";
import { PipelineStageCard } from "@/components/dashboard/pipeline-stage-card";
import { fetchApiHealth, fetchApiMeta } from "@/lib/api";
import { NavigationItem } from "@/types/navigation";

const navigationItems: NavigationItem[] = [
  {
    label: "Overview Dashboard",
    description: "System summary, metrics, and entry point for platform health.",
    badge: "Live",
    active: true,
  },
  {
    label: "Source Control",
    description: "Scraper initiation, source filters, and run monitoring.",
    badge: "Soon",
  },
  {
    label: "Evidence Explorer",
    description: "Raw and cleaned public feedback inspection surfaces.",
    badge: "Soon",
  },
  {
    label: "Pain Point Explorer",
    description: "Structured complaint analysis with taxonomy-level filters.",
    badge: "Soon",
  },
  {
    label: "Benchmarking",
    description: "Theme-wise comparison across Square Yards and competitors.",
    badge: "Soon",
  },
  {
    label: "Prioritization Board",
    description: "Issue scoring and action recommendation pipeline.",
    badge: "Soon",
  },
];

export default async function Home() {
  let apiStatus = "Unavailable";
  let apiSubtitle = "Backend not reachable";
  let apiVersion = "Unknown";
  let environment = "unknown";
  let appName = "Pain Intelligence";
  let apiPrefix = "/api/v1";

  try {
    const [health, meta] = await Promise.all([fetchApiHealth(), fetchApiMeta()]);
    apiStatus = health.status === "ok" ? "Connected" : health.status;
    apiSubtitle = `${health.app_name} • ${health.environment}`;
    apiVersion = meta.version;
    environment = meta.environment;
    appName = meta.app_name;
    apiPrefix = meta.api_prefix;
  } catch {
    apiStatus = "Unavailable";
    apiSubtitle = "Start the FastAPI service on port 8000";
    apiVersion = "N/A";
    environment = "offline";
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
          <HeroBanner apiStatus={apiStatus} apiSubtitle={apiSubtitle} />

          <section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <OverviewStatCard
              label="Application"
              value={appName}
              helper="Active frontend shell connected to live backend metadata."
            />
            <OverviewStatCard
              label="Environment"
              value={environment}
              helper="Pulled from centralized backend settings."
            />
            <OverviewStatCard
              label="API Prefix"
              value={apiPrefix}
              helper="Versioned route base ready for upcoming modules."
            />
            <OverviewStatCard
              label="Current Build Step"
              value="Step 3"
              helper="Polished frontend application shell in progress."
            />
          </section>

          <section className="mt-8 grid gap-6 xl:grid-cols-2">
            <NavPreviewCard
              title="Core Product Scope"
              description="This workspace is being shaped around the full public-signal product intelligence flow required for the Real Estate Pain Point Intelligence Platform."
              points={[
                "Multi-source public scraping across Reddit, app stores, X/Twitter, YouTube, and review sites",
                "Cleaning, multilingual normalization, and structured complaint extraction",
                "Journey-stage mapping, taxonomy clustering, and root-cause hypothesis generation",
                "Competitor benchmarking, prioritization logic, action recommendation, and export-ready outputs",
              ]}
            />

            <NavPreviewCard
              title="Planned Frontend Surfaces"
              description="The current shell prepares the visual and structural foundation for operational intelligence workflows."
              points={[
                "Live scrape run monitor and pipeline progress tracking",
                "Raw evidence explorer with cleaned record inspection",
                "Pain point explorer with category, severity, and stage filtering",
                "Review queue, export center, and Notion synchronization control panel",
              ]}
            />
          </section>

          <section className="mt-8">
            <div className="mb-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/45">
                Product pipeline preview
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-white">
                Planned multi-agent flow
              </h2>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-white/60">
                These are the key platform stages that will be progressively
                implemented in upcoming backend and frontend steps.
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <PipelineStageCard
                step="Stage 01"
                title="Source ingestion"
                description="Automated scrapers and source-specific collection strategies for public complaint signals."
              />
              <PipelineStageCard
                step="Stage 02"
                title="Normalization"
                description="Cleaning, deduplication, language handling, and entity normalization before analysis."
              />
              <PipelineStageCard
                step="Stage 03"
                title="Multi-agent analysis"
                description="Journey mapping, extraction, clustering, benchmarking, and root-cause hypothesis generation."
              />
              <PipelineStageCard
                step="Stage 04"
                title="Action outputs"
                description="Prioritization, review workflow, Notion sync, CSV/JSON/PDF exports, and decision-ready outputs."
              />
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}