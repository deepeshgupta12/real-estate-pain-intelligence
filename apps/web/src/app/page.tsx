import { SectionCard } from "@/components/section-card";
import { StatusCard } from "@/components/status-card";
import { fetchApiHealth } from "@/lib/api";

export default async function Home() {
  let apiStatus = "Unavailable";
  let apiSubtitle = "Backend not reachable";
  let apiVersion = "Unknown";

  try {
    const health = await fetchApiHealth();
    apiStatus = health.status === "ok" ? "Connected" : health.status;
    apiSubtitle = `${health.app_name} • ${health.environment}`;
    apiVersion = health.version;
  } catch {
    apiStatus = "Unavailable";
    apiSubtitle = "Start the FastAPI service on port 8000";
    apiVersion = "N/A";
  }

  return (
    <main className="min-h-screen">
      <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8">
        <header className="rounded-[32px] border border-white/10 bg-white/5 p-8 shadow-[0_20px_70px_rgba(0,0,0,0.28)] backdrop-blur">
          <div className="max-w-4xl">
            <div className="inline-flex rounded-full border border-cyan-400/30 bg-cyan-400/10 px-4 py-1 text-sm font-medium text-cyan-200">
              Foundation Build • Step 1
            </div>
            <h1 className="mt-5 text-4xl font-semibold leading-tight tracking-tight text-white md:text-6xl">
              Real Estate Pain Point Intelligence Platform
            </h1>
            <p className="mt-5 max-w-3xl text-base leading-7 text-white/70 md:text-lg">
              A multi-agent public Voice-of-Customer intelligence product built
              to extract real-estate user pain points, benchmark competitors,
              prioritize issues, and convert them into product-action
              recommendations for Square Yards web and app teams.
            </p>
          </div>
        </header>

        <section className="mt-8 grid gap-5 md:grid-cols-3">
          <StatusCard
            title="Backend API"
            value={apiStatus}
            subtitle={apiSubtitle}
          />
          <StatusCard
            title="API Version"
            value={apiVersion}
            subtitle="Health endpoint wired into frontend"
          />
          <StatusCard
            title="Build State"
            value="Step 1"
            subtitle="Repository foundation in progress"
          />
        </section>

        <section className="mt-8 grid gap-6 lg:grid-cols-2">
          <SectionCard
            title="Locked Product Scope"
            description="This product will scrape public signals from multiple sources, normalize them, process them through a multi-agent pipeline, and generate product recommendations, review workflows, exports, and Notion-ready outputs."
          >
            <div className="grid gap-3 text-sm text-white/75 sm:grid-cols-2">
              {[
                "Public-source scraping",
                "Streaming-aware orchestration",
                "Multilingual processing",
                "Journey-stage mapping",
                "Pain-point extraction",
                "Taxonomy and clustering",
                "Competitor benchmarking",
                "Prioritization engine",
                "Action recommendations",
                "Human review workflow",
                "Notion integration",
                "CSV / JSON / PDF exports",
              ].map((item) => (
                <div
                  key={item}
                  className="rounded-2xl border border-white/10 bg-black/10 px-4 py-3"
                >
                  {item}
                </div>
              ))}
            </div>
          </SectionCard>

          <SectionCard
            title="Planned Product Surfaces"
            description="The frontend will evolve into a polished intelligence workspace with operational monitoring, investigation tools, and decision-support interfaces."
          >
            <div className="space-y-3 text-sm text-white/75">
              {[
                "Overview dashboard with live health and system metrics",
                "Source scrape control center and run monitor",
                "Raw evidence explorer and cleaned evidence inspection",
                "Pain-point explorer and taxonomy views",
                "Cluster insight analysis workspace",
                "Competitor benchmark dashboard",
                "Prioritization board and action recommendation board",
                "Human review queue, export center, and Notion sync status",
              ].map((item) => (
                <div
                  key={item}
                  className="rounded-2xl border border-white/10 bg-black/10 px-4 py-3"
                >
                  {item}
                </div>
              ))}
            </div>
          </SectionCard>
        </section>

        <section className="mt-8">
          <SectionCard
            title="Implementation Discipline"
            description="This repository is being built in tightly controlled steps. Every step is tracked in the implementation tracker, tested locally, and confirmed before the next phase begins."
          >
            <div className="grid gap-4 md:grid-cols-4">
              {[
                ["Complete files only", "No patch fragments will be used."],
                ["Stepwise execution", "Each implementation step is isolated and testable."],
                ["Tracker-first workflow", "The tracker markdown remains the source of truth."],
                ["GitHub-ready structure", "The repo remains publishable from the start."],
              ].map(([title, desc]) => (
                <div
                  key={title}
                  className="rounded-2xl border border-white/10 bg-black/10 p-4"
                >
                  <h3 className="text-base font-semibold text-white">{title}</h3>
                  <p className="mt-2 text-sm leading-6 text-white/65">{desc}</p>
                </div>
              ))}
            </div>
          </SectionCard>
        </section>
      </div>
    </main>
  );
}