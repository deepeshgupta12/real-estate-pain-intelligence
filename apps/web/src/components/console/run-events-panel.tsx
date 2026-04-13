"use client";

import { useState } from "react";
import { RunEventResponse } from "@/lib/api";
import { SectionShell } from "@/components/console/section-shell";

type RunEventsPanelProps = {
  initialEvents: RunEventResponse[];
};

function getEventIcon(eventType: string | null | undefined): string {
  if (eventType === "dispatch") return "🚀";
  if (eventType === "start") return "▶️";
  if (eventType === "complete") return "✓";
  if (eventType === "fail") return "❌";
  return "•";
}

function getEventLabel(eventType: string | null | undefined): string {
  if (eventType === "dispatch") return "Session started";
  if (eventType === "start") return "Data collection began";
  if (eventType === "complete") return "Step completed successfully";
  if (eventType === "fail") return "Step failed";
  return eventType ?? "Unknown event";
}

function formatTime(timestamp: string | null | undefined): string {
  if (!timestamp) return "Unknown";
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMinutes = Math.floor((now.getTime() - date.getTime()) / 1000 / 60);

    if (diffMinutes < 1) return "just now";
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`;
    return date.toLocaleDateString();
  } catch {
    return timestamp.substring(0, 10);
  }
}

export function RunEventsPanel({ initialEvents }: RunEventsPanelProps) {
  const [events] = useState<RunEventResponse[]>(initialEvents);

  if (events.length === 0) {
    return (
      <SectionShell
        id="run-events"
        eyebrow="Timeline"
        title="Activity Log"
        description="Track session events and operations"
      >
        <div className="rounded-lg bg-slate-50 px-6 py-8 text-center text-slate-600">
          No activity yet.
        </div>
      </SectionShell>
    );
  }

  return (
    <SectionShell
      id="run-events"
      eyebrow="Timeline"
      title="Activity Log"
      description="Track session events and operations"
    >
      <div className="card p-6">
        <div className="space-y-4">
          {events.map((event, index) => {
            const icon = getEventIcon(event.event_type);
            const label = getEventLabel(event.event_type);
            const time = formatTime(event.created_at);

            return (
              <div key={index} className="flex gap-4 pb-4 border-b border-slate-200 last:border-b-0 last:pb-0">
                <div className="text-2xl shrink-0">{icon}</div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-slate-900">{label}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <p className="text-sm text-slate-600">Run #{event.scrape_run_id}</p>
                    <span className="text-slate-400">•</span>
                    <p className="text-sm text-slate-500">{time}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </SectionShell>
  );
}
