export type ApiHealthResponse = {
  status: string;
  app_name: string;
  environment: string;
  version: string;
  api_prefix: string;
};

export type ApiMetaResponse = {
  app_name: string;
  version: string;
  environment: string;
  api_prefix: string;
  frontend_url: string;
  docs_url: string;
  openapi_url: string;
};

export type ScrapeRunCreatePayload = {
  source_name: string;
  target_brand: string;
  status?: string;
  pipeline_stage?: string;
  trigger_mode?: string;
  items_discovered?: number;
  items_processed?: number;
  error_message?: string;
  orchestrator_notes?: string;
  started_at?: string | null;
  last_heartbeat_at?: string | null;
  completed_at?: string | null;
};

export type ScrapeRunResponse = {
  id: number;
  source_name: string;
  target_brand: string;
  status: string;
  pipeline_stage: string;
  trigger_mode: string;
  items_discovered: number;
  items_processed: number;
  error_message: string | null;
  orchestrator_notes: string | null;
  started_at: string | null;
  last_heartbeat_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type OrchestratorDispatchResponse = {
  run_id: number;
  status: string;
  pipeline_stage: string;
  trigger_mode: string;
  orchestrator_notes: string | null;
  started_at: string | null;
  last_heartbeat_at: string | null;
  completed_at: string | null;
};

export type FinalHardeningOverviewResponse = {
  runs_total: number;
  runs_completed: number;
  runs_failed: number;
  evidence_total: number;
  insights_total: number;
  retrieval_documents_total: number;
  review_queue_total: number;
  pending_review_total: number;
  approved_review_total: number;
  rejected_review_total: number;
  notion_jobs_total: number;
  export_jobs_total: number;
  run_events_total: number;
};

export type ObservabilityOverviewResponse = {
  runs_total: number;
  active_queue_count: number;
  stale_active_runs_count: number;
  recent_failed_runs_count: number;
  recent_events_count: number;
  review_backlog_count: number;
  run_events_total: number;
  runs_by_status: Record<string, number>;
  runs_by_stage: Record<string, number>;
};

export type QueueHealthItem = {
  run_id: number;
  source_name: string;
  target_brand: string;
  status: string;
  pipeline_stage: string;
  items_discovered: number;
  items_processed: number;
  last_heartbeat_at: string | null;
  orchestrator_notes: string | null;
  heartbeat_age_seconds: number | null;
  is_stale: boolean;
  health_label: string;
  latest_event_type: string | null;
  latest_event_at: string | null;
  latest_event_message: string | null;
};

export type RunEventResponse = {
  id: number;
  scrape_run_id: number;
  event_type: string;
  stage: string;
  status: string;
  message: string;
  payload_json: Record<string, unknown>;
  created_at: string;
};

export type StageTimelineItem = {
  stage: string;
  first_event_at: string;
  last_event_at: string;
  latest_status: string;
  event_count: number;
  duration_seconds: number;
};

export type RunDiagnosticsResponse = {
  run_id: number;
  source_name: string;
  target_brand: string;
  status: string;
  pipeline_stage: string;
  trigger_mode: string;
  items_discovered: number;
  items_processed: number;
  started_at: string | null;
  last_heartbeat_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  error_message: string | null;
  orchestrator_notes: string | null;
  heartbeat_age_seconds: number | null;
  is_stale: boolean;
  health_label: string;
  total_events: number;
  latest_event: {
    id: number;
    event_type: string;
    stage: string;
    status: string;
    message: string;
    created_at: string;
  } | null;
  stage_timeline: StageTimelineItem[];
  readiness_checks: Record<string, boolean>;
  readiness_counts: Record<string, number>;
  failure_snapshot: {
    failed: boolean;
    error_message: string | null;
    failed_at: string | null;
    failed_stage: string | null;
    failed_event_message: string | null;
    last_successful_stage: string | null;
  };
  metadata: {
    stale_threshold_seconds: number;
  };
};

export type RunNormalizationResponse = {
  run_id: number;
  total_evidence: number;
  normalized_count: number;
  pending_count: number;
  failed_count: number;
  pipeline_stage: string;
  status: string;
  orchestrator_notes: string | null;
};

export type RunMultilingualResponse = {
  run_id: number;
  total_evidence: number;
  processed_count: number;
  pending_count: number;
  failed_count: number;
  pipeline_stage: string;
  status: string;
  orchestrator_notes: string | null;
};

export type RunIntelligenceResponse = {
  run_id: number;
  total_evidence: number;
  insights_generated: number;
  llm_generated_count: number;
  deterministic_generated_count: number;
  failed_count: number;
  pipeline_stage: string;
  status: string;
  orchestrator_notes: string | null;
};

export type AgentInsightResponse = {
  id: number;
  scrape_run_id: number;
  raw_evidence_id: number;
  journey_stage: string | null;
  pain_point_label: string | null;
  pain_point_summary: string | null;
  taxonomy_cluster: string | null;
  root_cause_hypothesis: string | null;
  competitor_label: string | null;
  priority_label: string | null;
  action_recommendation: string | null;
  confidence_score: string | null;
  insight_status: string;
  created_at: string;
};

export type RetrievalIndexResponse = {
  run_id: number;
  indexed_count: number;
  pipeline_stage: string;
  status: string;
  orchestrator_notes: string | null;
};

export type HumanReviewGenerateResponse = {
  run_id: number;
  generated_count: number;
  pipeline_stage: string;
  status: string;
  orchestrator_notes: string | null;
};

export type NotionSyncGenerateResponse = {
  run_id: number;
  generated_count: number;
  pipeline_stage: string;
  status: string;
  orchestrator_notes: string | null;
};

export type NotionSyncExecutionSummaryResponse = {
  run_id: number;
  attempted_count: number;
  synced_count: number;
  failed_count: number;
  retrying_count: number;
  pipeline_stage: string;
  status: string;
  orchestrator_notes: string | null;
};

export type ExportGenerateResponse = {
  run_id: number;
  generated_count: number;
  pipeline_stage: string;
  status: string;
  orchestrator_notes: string | null;
};

export type ExportJobResponse = {
  id: number;
  scrape_run_id: number;
  export_format: string;
  export_status: string;
  file_name: string | null;
  file_path: string | null;
  file_size_bytes: number | null;
  row_count: number | null;
  generated_at: string | null;
  export_notes: string | null;
  completed_at: string | null;
  created_at: string;
};

export type RunReadinessResponse = {
  run_id: number;
  status: string;
  pipeline_stage: string;
  ready_for_finalization: boolean;
  checks: {
    has_evidence: boolean;
    normalization_ready: boolean;
    multilingual_ready: boolean;
    intelligence_ready: boolean;
    retrieval_ready: boolean;
    human_review_ready: boolean;
    review_console_ready: boolean;
    notion_ready: boolean;
    export_ready: boolean;
    run_not_failed: boolean;
  };
  counts: {
    evidence_count: number;
    normalized_count: number;
    multilingual_count: number;
    insight_count: number;
    retrieval_count: number;
    embedded_retrieval_count: number;
    review_count: number;
    pending_review_count: number;
    approved_review_count: number;
    rejected_review_count: number;
    notion_sync_count: number;
    export_count: number;
    run_event_count: number;
  };
};

export type ReviewSummaryResponse = {
  run_id: number | null;
  total_items: number;
  pending_review_count: number;
  reviewed_count: number;
  approved_count: number;
  rejected_count: number;
  high_priority_count: number;
  llm_assisted_count: number;
  deterministic_count: number;
};

export type AgentInsightSnapshot = {
  id: number;
  raw_evidence_id: number;
  journey_stage: string | null;
  pain_point_label: string | null;
  pain_point_summary: string | null;
  taxonomy_cluster: string | null;
  root_cause_hypothesis: string | null;
  competitor_label: string | null;
  priority_label: string | null;
  action_recommendation: string | null;
  confidence_score: string | null;
  insight_status: string;
  analysis_mode: string | null;
  llm_attempted: boolean | null;
  llm_used: boolean | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export type EvidenceSnapshot = {
  id: number;
  source_name: string;
  platform_name: string;
  content_type: string;
  source_url: string | null;
  published_at: string | null;
  language: string | null;
  resolved_language: string | null;
  normalization_status: string;
  multilingual_status: string;
  evidence_excerpt: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export type ReviewQueueItem = {
  id: number;
  scrape_run_id: number;
  agent_insight_id: number;
  review_status: string;
  reviewer_decision: string | null;
  reviewer_notes: string | null;
  source_summary: string | null;
  priority_label: string | null;
  metadata_json: Record<string, unknown>;
  reviewed_at: string | null;
  created_at: string;
  insight_snapshot?: AgentInsightSnapshot | null;
  evidence_snapshot?: EvidenceSnapshot | null;
};

export type BulkReviewActionResponse = {
  updated_count: number;
  reviewer_decision: string;
  item_ids: number[];
};

export type ReviewDecisionPayload = {
  reviewer_notes?: string;
};

export type BulkReviewPayload = {
  item_ids: number[];
  reviewer_notes?: string;
};

export type ExportGeneratePayload = {
  export_formats: string[];
};

export type ScrapeExecutionFetchModeSummary = {
  live_fetch_enabled: boolean;
  fail_open_to_stub: boolean;
  live_items_count: number;
  stub_items_count: number;
  unknown_items_count: number;
};

export type ScrapeExecutionResponse = {
  run_id: number;
  source_name: string;
  target_brand: string;
  status: string;
  pipeline_stage: string;
  items_discovered: number;
  items_processed: number;
  persisted_evidence_count: number;
  deduplicated_count: number;
  orchestrator_notes: string | null;
  fetch_mode_summary: ScrapeExecutionFetchModeSummary;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

type FetchOptions = RequestInit & {
  query?: Record<string, string | number | boolean | undefined | null>;
};

function buildUrl(path: string, query?: FetchOptions["query"]): string {
  const url = new URL(`${API_BASE_URL}${path}`);

  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    });
  }

  return url.toString();
}

function buildErrorMessage(path: string, message: string): string {
  try {
    const parsed = JSON.parse(message) as {
      detail?: string | Array<{ msg: string; loc?: string[] }>;
    };
    if (parsed.detail) {
      // FastAPI returns a plain string detail for most errors
      if (typeof parsed.detail === "string") {
        return parsed.detail;
      }
      // FastAPI 422 Unprocessable Entity returns an array of validation errors
      if (Array.isArray(parsed.detail)) {
        return parsed.detail
          .map((e) => {
            const field = e.loc ? e.loc.filter((l) => l !== "body").join(".") : "";
            return field ? `${field}: ${e.msg}` : e.msg;
          })
          .join(" · ");
      }
    }
  } catch {
    // Ignore JSON parsing failure and fall back to raw text.
  }

  return message || `Failed to fetch ${path}`;
}

async function fetchJson<T>(path: string, options?: FetchOptions): Promise<T> {
  const response = await fetch(buildUrl(path, options?.query), {
    cache: "no-store",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(buildErrorMessage(path, message));
  }

  return response.json();
}

export async function fetchApiHealth(): Promise<ApiHealthResponse> {
  return fetchJson<ApiHealthResponse>("/api/v1/health");
}

export async function fetchApiMeta(): Promise<ApiMetaResponse> {
  return fetchJson<ApiMetaResponse>("/api/v1/meta");
}

export async function fetchSupportedSources(): Promise<string[]> {
  return fetchJson<string[]>("/api/v1/scrape-execution/sources");
}

export async function createScrapeRun(
  payload: ScrapeRunCreatePayload,
): Promise<ScrapeRunResponse> {
  return fetchJson<ScrapeRunResponse>("/api/v1/runs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchScrapeRuns(): Promise<ScrapeRunResponse[]> {
  return fetchJson<ScrapeRunResponse[]>("/api/v1/runs");
}

export async function fetchScrapeRun(runId: number): Promise<ScrapeRunResponse> {
  return fetchJson<ScrapeRunResponse>(`/api/v1/runs/${runId}`);
}

export async function dispatchRun(
  runId: number,
): Promise<OrchestratorDispatchResponse> {
  return fetchJson<OrchestratorDispatchResponse>(
    `/api/v1/orchestrator/dispatch/${runId}`,
    {
      method: "POST",
    },
  );
}

export async function startRun(
  runId: number,
): Promise<OrchestratorDispatchResponse> {
  return fetchJson<OrchestratorDispatchResponse>(
    `/api/v1/orchestrator/start/${runId}`,
    {
      method: "POST",
    },
  );
}

export async function fetchFinalHardeningOverview(): Promise<FinalHardeningOverviewResponse> {
  return fetchJson<FinalHardeningOverviewResponse>("/api/v1/final-hardening/overview");
}

export async function fetchObservabilityOverview(): Promise<ObservabilityOverviewResponse> {
  return fetchJson<ObservabilityOverviewResponse>("/api/v1/final-hardening/observability");
}

export async function fetchQueueHealth(): Promise<QueueHealthItem[]> {
  return fetchJson<QueueHealthItem[]>("/api/v1/orchestrator/queue");
}

export async function fetchRunDiagnostics(runId: number): Promise<RunDiagnosticsResponse> {
  return fetchJson<RunDiagnosticsResponse>(`/api/v1/orchestrator/diagnostics/${runId}`);
}

export async function fetchRunReadiness(runId: number): Promise<RunReadinessResponse> {
  return fetchJson<RunReadinessResponse>(`/api/v1/final-hardening/readiness/${runId}`);
}

export async function executeScrapeRun(
  runId: number,
): Promise<ScrapeExecutionResponse> {
  return fetchJson<ScrapeExecutionResponse>(`/api/v1/scrape-execution/${runId}`, {
    method: "POST",
  });
}

export async function normalizeRun(
  runId: number,
): Promise<RunNormalizationResponse> {
  return fetchJson<RunNormalizationResponse>(`/api/v1/normalization/${runId}`, {
    method: "POST",
  });
}

export async function processMultilingualRun(
  runId: number,
): Promise<RunMultilingualResponse> {
  return fetchJson<RunMultilingualResponse>(`/api/v1/multilingual/${runId}`, {
    method: "POST",
  });
}

export async function processRunIntelligence(
  runId: number,
): Promise<RunIntelligenceResponse> {
  return fetchJson<RunIntelligenceResponse>(`/api/v1/intelligence/${runId}`, {
    method: "POST",
  });
}

export async function indexRunRetrieval(
  runId: number,
): Promise<RetrievalIndexResponse> {
  return fetchJson<RetrievalIndexResponse>(`/api/v1/retrieval/index/${runId}`, {
    method: "POST",
  });
}

export async function generateHumanReviewQueue(
  runId: number,
): Promise<HumanReviewGenerateResponse> {
  return fetchJson<HumanReviewGenerateResponse>(`/api/v1/human-review/generate/${runId}`, {
    method: "POST",
  });
}

export async function generateNotionSyncJobs(
  runId: number,
): Promise<NotionSyncGenerateResponse> {
  return fetchJson<NotionSyncGenerateResponse>(`/api/v1/notion-sync/generate/${runId}`, {
    method: "POST",
  });
}

export async function executeNotionSyncJobsForRun(
  runId: number,
): Promise<NotionSyncExecutionSummaryResponse> {
  return fetchJson<NotionSyncExecutionSummaryResponse>(`/api/v1/notion-sync/execute-run/${runId}`, {
    method: "POST",
  });
}

export async function generateExportJobs(
  runId: number,
  payload: ExportGeneratePayload,
): Promise<ExportGenerateResponse> {
  return fetchJson<ExportGenerateResponse>(`/api/v1/exports/generate/${runId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchRunInsights(runId: number): Promise<AgentInsightResponse[]> {
  return fetchJson<AgentInsightResponse[]>(`/api/v1/intelligence/${runId}`);
}

export async function fetchExportJobs(runId: number): Promise<ExportJobResponse[]> {
  return fetchJson<ExportJobResponse[]>(`/api/v1/exports?run_id=${runId}`);
}

export function getExportDownloadUrl(exportJobId: number): string {
  return `/api/v1/exports/download/${exportJobId}`;
}

export async function fetchRunEvents(params?: {
  runId?: number;
  eventType?: string;
  stage?: string;
  status?: string;
  limit?: number;
  offset?: number;
  newestFirst?: boolean;
}): Promise<RunEventResponse[]> {
  if (params?.runId) {
    return fetchJson<RunEventResponse[]>(`/api/v1/run-events/${params.runId}`, {
      query: {
        event_type: params.eventType,
        stage: params.stage,
        status: params.status,
        limit: params.limit,
        offset: params.offset,
        newest_first: params.newestFirst,
      },
    });
  }

  return fetchJson<RunEventResponse[]>("/api/v1/run-events", {
    query: {
      event_type: params?.eventType,
      stage: params?.stage,
      status: params?.status,
      limit: params?.limit,
      offset: params?.offset,
      newest_first: params?.newestFirst,
    },
  });
}

export async function fetchReviewSummary(runId?: number): Promise<ReviewSummaryResponse> {
  return fetchJson<ReviewSummaryResponse>("/api/v1/human-review/summary", {
    query: { run_id: runId },
  });
}

export async function fetchReviewQueue(params?: {
  runId?: number;
  reviewStatus?: string;
  reviewerDecision?: string;
  priorityLabel?: string;
  analysisMode?: string;
  includeDetails?: boolean;
  limit?: number;
  offset?: number;
}): Promise<ReviewQueueItem[]> {
  return fetchJson<ReviewQueueItem[]>("/api/v1/human-review", {
    query: {
      run_id: params?.runId,
      review_status: params?.reviewStatus,
      reviewer_decision: params?.reviewerDecision,
      priority_label: params?.priorityLabel,
      analysis_mode: params?.analysisMode,
      include_details: params?.includeDetails,
      limit: params?.limit,
      offset: params?.offset,
    },
  });
}

export async function fetchReviewDetail(reviewItemId: number): Promise<ReviewQueueItem> {
  return fetchJson<ReviewQueueItem>(`/api/v1/human-review/detail/${reviewItemId}`);
}

export async function approveReviewItem(
  reviewItemId: number,
  payload: ReviewDecisionPayload,
): Promise<ReviewQueueItem> {
  return fetchJson<ReviewQueueItem>(`/api/v1/human-review/approve/${reviewItemId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function rejectReviewItem(
  reviewItemId: number,
  payload: ReviewDecisionPayload,
): Promise<ReviewQueueItem> {
  return fetchJson<ReviewQueueItem>(`/api/v1/human-review/reject/${reviewItemId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function bulkApproveReviewItems(
  payload: BulkReviewPayload,
): Promise<BulkReviewActionResponse> {
  return fetchJson<BulkReviewActionResponse>("/api/v1/human-review/bulk/approve", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function bulkRejectReviewItems(
  payload: BulkReviewPayload,
): Promise<BulkReviewActionResponse> {
  return fetchJson<BulkReviewActionResponse>("/api/v1/human-review/bulk/reject", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ---------------------------------------------------------------------------
// Evidence Explorer (P13)
// ---------------------------------------------------------------------------

export type RawEvidenceResponse = {
  id: number;
  scrape_run_id: number;
  source_name: string;
  platform_name: string;
  content_type: string;
  external_id: string | null;
  author_name: string | null;
  source_url: string | null;
  published_at: string | null;
  fetched_at: string | null;
  source_query: string | null;
  parser_version: string | null;
  raw_text: string | null;
  cleaned_text: string | null;
  language: string | null;
  resolved_language: string | null;
  normalization_status: string;
  multilingual_status: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export async function fetchEvidence(params?: {
  runId?: number;
  sourceName?: string;
  contentType?: string;
  limit?: number;
}): Promise<RawEvidenceResponse[]> {
  return fetchJson<RawEvidenceResponse[]>("/api/v1/evidence", {
    query: {
      run_id: params?.runId,
      source_name: params?.sourceName,
      content_type: params?.contentType,
      limit: params?.limit ?? 100,
    },
  });
}

// ---------------------------------------------------------------------------
// Retrieval Search (P14)
// ---------------------------------------------------------------------------

export type RetrievalSearchResult = {
  retrieval_document_id: number;
  scrape_run_id: number;
  raw_evidence_id: number | null;
  agent_insight_id: number | null;
  title: string | null;
  document_type: string;
  language_code: string | null;
  score: number;
  score_type: string;
  document_text: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export async function searchRetrieval(params: {
  query: string;
  topK?: number;
  runId?: number;
}): Promise<RetrievalSearchResult[]> {
  return fetchJson<RetrievalSearchResult[]>("/api/v1/retrieval/search", {
    method: "POST",
    body: JSON.stringify({
      query: params.query,
      top_k: params.topK ?? 5,
      run_id: params.runId ?? null,
    }),
  });
}