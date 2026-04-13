"use client";

import { useState } from "react";
import { InfoTip } from "@/components/ui/info-tip";
import { ScrapeRunCreatePayload, ScrapeRunResponse } from "@/lib/api";
import { SectionShell } from "@/components/console/section-shell";

type RunSetupPanelProps = {
  availableSources: string[];
  runs: ScrapeRunResponse[];
  currentRunId: number | null;
  loading: boolean;
  onCreateRun: (payload: ScrapeRunCreatePayload) => Promise<void>;
  onSelectRun: (runId: number) => Promise<void>;
};

export function RunSetupPanel({
  availableSources,
  runs,
  currentRunId,
  loading,
  onCreateRun,
  onSelectRun,
}: RunSetupPanelProps) {
  const [sourceName, setSourceName] = useState(availableSources[0] ?? "reddit");
  const [brandName, setBrandName] = useState("");
  const [startType, setStartType] = useState("manual");
  const [notes, setNotes] = useState("");

  async function handleCreateRun() {
    if (!brandName.trim()) {
      return;
    }

    await onCreateRun({
      source_name: sourceName,
      target_brand: brandName.trim(),
      status: "created",
      pipeline_stage: "created",
      trigger_mode: startType,
      items_discovered: 0,
      items_processed: 0,
      orchestrator_notes: notes.trim() || undefined,
    });

    setBrandName("");
    setNotes("");
  }

  return (
    <SectionShell
      id="run-workspace"
      eyebrow="Start here"
      title="Run setup"
      description="Create a new run or load an older one. The labels below are written in simple product language so the workflow is easier to understand and operate."
    >
      <div className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="rounded-3xl border border-white/10 bg-black/10 p-5">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-white">Create a new run</h3>
            <InfoTip
              title="What is a run?"
              description="A run is one full processing journey for one source and one target brand. It keeps all collected feedback, progress, review output, and final files together."
            />
          </div>

          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <div>
              <label className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-white/45">
                Feedback source
                <InfoTip
                  title="Feedback source"
                  description="Choose where the public feedback will come from, such as Reddit, YouTube, app reviews, or review websites."
                />
              </label>
              <select
                value={sourceName}
                onChange={(e) => setSourceName(e.target.value)}
                className="mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none"
              >
                {availableSources.map((source) => (
                  <option key={source} value={source}>
                    {source}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-white/45">
                Run start type
                <InfoTip
                  title="Run start type"
                  description="This is just a simple label for how the run was started. For now, manual is the normal option."
                />
              </label>
              <select
                value={startType}
                onChange={(e) => setStartType(e.target.value)}
                className="mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none"
              >
                <option value="manual">manual</option>
                <option value="scheduled">scheduled</option>
                <option value="api">api</option>
              </select>
            </div>
          </div>

          <div className="mt-4">
            <label className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-white/45">
              Brand or product name
              <InfoTip
                title="Brand or product name"
                description="This is the brand you want to analyze. The backend stores this as the target brand for the run."
              />
            </label>
            <input
              value={brandName}
              onChange={(e) => setBrandName(e.target.value)}
              placeholder="Example: Square Yards"
              className="mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none placeholder:text-white/35"
            />
          </div>

          <div className="mt-4">
            <label className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-white/45">
              Optional notes
              <InfoTip
                title="Optional notes"
                description="Use this for quick context like the purpose of the run, test notes, or what you want to check after processing."
              />
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              placeholder="Example: Test run for review quality on stale listings and agent response problems"
              className="mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none placeholder:text-white/35"
            />
          </div>

          <div className="mt-4">
            <button
              type="button"
              onClick={handleCreateRun}
              disabled={loading || !brandName.trim()}
              className="rounded-2xl border border-cyan-400/30 bg-cyan-400/10 px-5 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-400/15 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "Creating..." : "Create run"}
            </button>
          </div>
        </div>

        <div className="rounded-3xl border border-white/10 bg-black/10 p-5">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-white">Load an existing run</h3>
            <InfoTip
              title="Load an existing run"
              description="Pick an older run to continue processing, inspect progress, or review results without creating a new one."
            />
          </div>

          <div className="mt-5 space-y-3">
            {runs.length === 0 ? (
              <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-6 text-sm text-white/60">
                No runs available yet. Create your first run from the left panel.
              </div>
            ) : (
              runs.slice(0, 8).map((run) => {
                const isActive = currentRunId === run.id;

                return (
                  <button
                    key={run.id}
                    type="button"
                    onClick={() => onSelectRun(run.id)}
                    disabled={loading}
                    className={`w-full rounded-2xl border px-4 py-4 text-left transition ${
                      isActive
                        ? "border-cyan-400/30 bg-cyan-400/10"
                        : "border-white/10 bg-white/5 hover:bg-white/7"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-sm font-semibold text-white">
                          Run #{run.id} • {run.target_brand}
                        </p>
                        <p className="mt-1 text-xs text-white/55">
                          Source: {run.source_name} • Status: {run.status}
                        </p>
                        <p className="mt-2 text-xs text-white/45">
                          Current stage: {run.pipeline_stage}
                        </p>
                      </div>

                      {isActive ? (
                        <span className="rounded-full border border-cyan-300/25 bg-cyan-300/10 px-2 py-1 text-[10px] uppercase tracking-wide text-cyan-100">
                          Active
                        </span>
                      ) : null}
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>
      </div>
    </SectionShell>
  );
}