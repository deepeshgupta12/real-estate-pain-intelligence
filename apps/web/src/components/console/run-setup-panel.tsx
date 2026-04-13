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

function humanize(value: string): string {
  return value.replaceAll("_", " ");
}

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
      eyebrow="Run operations"
      title="Create or load a run"
      description="Start a new processing run or switch to an existing run. This section is intentionally compact so the active workflow remains visible without too much scrolling."
    >
      <div className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="workspace-soft rounded-3xl p-5">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-white">Create new run</h3>
            <InfoTip
              title="What is a run?"
              description="A run is one complete pipeline journey for one source and one target brand."
            />
          </div>

          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <div>
              <label className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-white/40">
                Feedback source
                <InfoTip
                  title="Feedback source"
                  description="Choose the public source that will feed evidence into the run."
                />
              </label>
              <select
                value={sourceName}
                onChange={(e) => setSourceName(e.target.value)}
                className="field-shell mt-2 w-full rounded-2xl px-4 py-3 text-sm"
              >
                {availableSources.map((source) => (
                  <option key={source} value={source}>
                    {humanize(source)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-white/40">
                Start type
                <InfoTip
                  title="Run start type"
                  description="This is the initiation mode stored against the run."
                />
              </label>
              <select
                value={startType}
                onChange={(e) => setStartType(e.target.value)}
                className="field-shell mt-2 w-full rounded-2xl px-4 py-3 text-sm"
              >
                <option value="manual">Manual</option>
                <option value="scheduled">Scheduled</option>
                <option value="api">API</option>
              </select>
            </div>
          </div>

          <div className="mt-4">
            <label className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-white/40">
              Brand or product
              <InfoTip
                title="Brand or product"
                description="This is the product or company that the feedback will be analyzed for."
              />
            </label>
            <input
              value={brandName}
              onChange={(e) => setBrandName(e.target.value)}
              placeholder="Example: Square Yards"
              className="field-shell mt-2 w-full rounded-2xl px-4 py-3 text-sm"
            />
          </div>

          <div className="mt-4">
            <label className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-white/40">
              Optional note
              <InfoTip
                title="Optional note"
                description="Use this for test context, objective, or reminder text."
              />
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={4}
              placeholder="Example: Check stale-listings signals and delayed agent follow-up quality."
              className="field-shell mt-2 w-full rounded-2xl px-4 py-3 text-sm"
            />
          </div>

          <div className="mt-5 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={handleCreateRun}
              disabled={loading || !brandName.trim()}
              className="rounded-2xl border border-cyan-400/28 bg-cyan-400/12 px-5 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-400/18 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "Creating..." : "Create run"}
            </button>
          </div>
        </div>

        <div className="workspace-soft rounded-3xl p-5">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-white">Existing runs</h3>
            <InfoTip
              title="Existing runs"
              description="Switch to an older run to continue operating it or inspect its output."
            />
          </div>

          <div className="mt-5 space-y-3">
            {runs.length === 0 ? (
              <div className="workspace-soft rounded-2xl px-4 py-6 text-sm text-white/58">
                No runs available yet. Create the first run from the panel on the left.
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
                        ? "border-cyan-400/24 bg-cyan-400/10"
                        : "border-white/8 bg-white/2.5 hover:border-white/14 hover:bg-white/4"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-white">
                          Run #{run.id} • {run.target_brand}
                        </p>
                        <p className="mt-1 text-xs text-white/52">
                          {humanize(run.source_name)} • {humanize(run.status)}
                        </p>
                        <p className="mt-2 text-xs text-white/42">
                          Stage: {humanize(run.pipeline_stage)}
                        </p>
                      </div>

                      {isActive ? (
                        <span className="badge badge-info shrink-0">Active</span>
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