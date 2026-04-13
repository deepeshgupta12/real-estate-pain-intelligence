"use client";

import { useEffect, useState } from "react";
import { fetchExportJobs, getExportDownloadUrl, type ExportJobResponse } from "@/lib/api";

type ExportsPanelProps = {
  runId: number | null;
  triggerRefresh?: number; // bump this to force a re-fetch after generate
};

const FORMAT_LABELS: Record<string, string> = {
  csv: "CSV",
  json: "JSON",
  pdf: "PDF",
};

const FORMAT_ICONS: Record<string, string> = {
  csv: "📊",
  json: "📋",
  pdf: "📄",
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function ExportsPanel({ runId, triggerRefresh }: ExportsPanelProps) {
  const [jobs, setJobs] = useState<ExportJobResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!runId) return;
    setLoading(true);
    setError("");
    fetchExportJobs(runId)
      .then(setJobs)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load exports"))
      .finally(() => setLoading(false));
  }, [runId, triggerRefresh]);

  if (!runId) {
    return (
      <section className="card p-6">
        <p className="text-[11px] font-semibold uppercase tracking-widest text-blue-600">Exports</p>
        <h2 className="mt-1 text-lg font-semibold text-slate-900">Download Files</h2>
        <p className="mt-3 text-sm text-slate-500">Load a session to see export files.</p>
      </section>
    );
  }

  const completed = jobs.filter((j) => j.export_status === "completed");
  const pending = jobs.filter((j) => j.export_status !== "completed");

  return (
    <section className="card p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-widest text-blue-600">Exports</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-900">Download Files</h2>
          <p className="mt-0.5 text-sm text-slate-500">
            Files generated for Run #{runId}. Use "Create Exports" in Run Steps to generate them.
          </p>
        </div>
        {loading && (
          <span className="text-xs text-slate-400">Loading…</span>
        )}
      </div>

      {error && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {!loading && jobs.length === 0 && (
        <div className="mt-6 rounded-lg border border-dashed border-slate-200 bg-slate-50 px-6 py-8 text-center">
          <p className="text-2xl">📂</p>
          <p className="mt-2 text-sm font-medium text-slate-700">No export files yet</p>
          <p className="mt-1 text-xs text-slate-500">
            Run "Step 7: Create Exports" in the Run Steps panel to generate CSV, JSON, and PDF files.
          </p>
        </div>
      )}

      {completed.length > 0 && (
        <div className="mt-5 space-y-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Ready to download</p>
          {completed.map((job) => (
            <div
              key={job.id}
              className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3 shadow-sm"
            >
              <div className="flex items-center gap-3">
                <span className="text-xl">{FORMAT_ICONS[job.export_format] ?? "📁"}</span>
                <div>
                  <p className="text-sm font-semibold text-slate-900">
                    {FORMAT_LABELS[job.export_format] ?? job.export_format.toUpperCase()} Export
                  </p>
                  <p className="text-xs text-slate-500">
                    {job.file_name ?? "export file"}
                    {job.file_size_bytes != null && ` · ${formatBytes(job.file_size_bytes)}`}
                    {job.row_count != null && ` · ${job.row_count} rows`}
                  </p>
                </div>
              </div>
              <a
                href={getExportDownloadUrl(job.id)}
                download={job.file_name ?? true}
                className="rounded-lg border border-blue-300 bg-blue-50 px-4 py-2 text-sm font-semibold text-blue-700 shadow-sm transition hover:bg-blue-100"
              >
                ↓ Download
              </a>
            </div>
          ))}
        </div>
      )}

      {pending.length > 0 && (
        <div className="mt-5 space-y-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Pending</p>
          {pending.map((job) => (
            <div
              key={job.id}
              className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-4 py-3"
            >
              <div className="flex items-center gap-3">
                <span className="text-xl">{FORMAT_ICONS[job.export_format] ?? "📁"}</span>
                <div>
                  <p className="text-sm font-medium text-slate-700">
                    {FORMAT_LABELS[job.export_format] ?? job.export_format.toUpperCase()} Export
                  </p>
                  <p className="text-xs text-slate-400 capitalize">{job.export_status}</p>
                </div>
              </div>
              <span className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">
                Processing
              </span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
