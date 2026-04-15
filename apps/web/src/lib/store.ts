/**
 * Global application state managed by Zustand.
 *
 * Zustand provides a lightweight, hook-based state management solution that
 * avoids prop drilling. This store holds the currently active run and related
 * UI state that multiple components need to read or update independently.
 *
 * Usage:
 *   import { useAppStore } from "@/lib/store";
 *   const { currentRunId, setCurrentRunId } = useAppStore();
 *
 * The store is intentionally kept minimal — per-component ephemeral state
 * (loading flags, error messages, local form state) stays in useState.
 */

import { create } from "zustand";
import type { ScrapeRunItem } from "@/lib/api";

// ── Types ──────────────────────────────────────────────────────────────────────

export type RunState = {
  /** The currently selected/active scrape run ID, or null if none selected. */
  currentRunId: number | null;

  /** Full ScrapeRunItem for the active run (loaded from API). */
  currentRun: ScrapeRunItem | null;

  /**
   * Monotonically increasing key — increment to force insight panel re-fetch
   * without changing runId (e.g. after the Analyze step completes).
   */
  insightRefreshKey: number;

  /**
   * Monotonically increasing key — increment to force export panel re-fetch
   * (e.g. after the Create Exports step completes).
   */
  exportRefreshKey: number;

  /** True while a pipeline action (scrape, analyze, etc.) is in progress. */
  isPipelineRunning: boolean;

  /** The last pipeline error message, or empty string if none. */
  lastPipelineError: string;
};

export type RunActions = {
  setCurrentRunId: (id: number | null) => void;
  setCurrentRun: (run: ScrapeRunItem | null) => void;
  triggerInsightRefresh: () => void;
  triggerExportRefresh: () => void;
  setPipelineRunning: (running: boolean) => void;
  setLastPipelineError: (message: string) => void;
  clearPipelineError: () => void;
  /** Reset all run state (called when user selects a new run). */
  resetRunState: () => void;
};

// ── Store ──────────────────────────────────────────────────────────────────────

const initialRunState: RunState = {
  currentRunId: null,
  currentRun: null,
  insightRefreshKey: 0,
  exportRefreshKey: 0,
  isPipelineRunning: false,
  lastPipelineError: "",
};

export const useAppStore = create<RunState & RunActions>((set) => ({
  ...initialRunState,

  setCurrentRunId: (id) =>
    set({ currentRunId: id }),

  setCurrentRun: (run) =>
    set({ currentRun: run, currentRunId: run?.id ?? null }),

  triggerInsightRefresh: () =>
    set((state) => ({ insightRefreshKey: state.insightRefreshKey + 1 })),

  triggerExportRefresh: () =>
    set((state) => ({ exportRefreshKey: state.exportRefreshKey + 1 })),

  setPipelineRunning: (running) =>
    set({ isPipelineRunning: running }),

  setLastPipelineError: (message) =>
    set({ lastPipelineError: message }),

  clearPipelineError: () =>
    set({ lastPipelineError: "" }),

  resetRunState: () =>
    set({
      currentRunId: null,
      currentRun: null,
      insightRefreshKey: 0,
      exportRefreshKey: 0,
      isPipelineRunning: false,
      lastPipelineError: "",
    }),
}));

// ── Convenience selectors ──────────────────────────────────────────────────────
// These prevent unnecessary re-renders by selecting only what a component needs.

/** Select only the current run ID (avoids re-render when other state changes). */
export const useCurrentRunId = () => useAppStore((s) => s.currentRunId);

/** Select the full current run object. */
export const useCurrentRun = () => useAppStore((s) => s.currentRun);

/** Select the insight refresh key. */
export const useInsightRefreshKey = () => useAppStore((s) => s.insightRefreshKey);

/** Select the export refresh key. */
export const useExportRefreshKey = () => useAppStore((s) => s.exportRefreshKey);

/** Select pipeline running state. */
export const useIsPipelineRunning = () => useAppStore((s) => s.isPipelineRunning);

/** Select the last pipeline error. */
export const useLastPipelineError = () => useAppStore((s) => s.lastPipelineError);
