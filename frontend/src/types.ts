export type ExtractionStatus =
  | 'queued'
  | 'running'
  | 'validated'
  | 'completed'
  | 'failure';

export type HealthState = 'healthy' | 'warning' | 'degraded' | 'offline' | 'unknown';

export interface HealthResponse {
  status: HealthState;
  components: {
    api: HealthState;
    database: HealthState;
    disk: HealthState;
    llm_provider: HealthState;
  };
  timestamp: string;
  uptime_seconds: number;
  [key: string]: unknown;
}

export interface MetricsResponse {
  total_requests: number;
  success_rate: number;
  average_latency_ms: number;
  schema_valid_pct: number;
  repair_success_rate: number;
  repair_attempts: number;
  failure_breakdown: { reason: string; count: number }[];
  latency_history: { t: string; latency: number }[];
  success_history: { t: string; rate: number }[];
  retry_history: { t: string; retries: number }[];
  [key: string]: unknown;
}

export interface PipelineStage {
  id: string;
  label: string;
  description: string;
  status: 'pending' | 'active' | 'done' | 'error';
}

export interface RepairAttempt {
  attempt: number;
  status: 'success' | 'failed';
  error: string | null;
}

export interface ExtractionResult {
  id: string;
  ticket: string;
  cleaned_text: string;
  structured_extraction: Record<string, unknown>;
  final_json: Record<string, unknown>;
  repair_attempts: RepairAttempt[];
  metadata: {
    provider: string;
    model: string;
    latency_ms: number;
    confidence: number;
    timestamp: string;
    repair_attempts: number;
  };
  status: ExtractionStatus;
}

export interface HistoryItem {
  id: string;
  request_id: string;
  ticket_id: string;
  timestamp: string;
  status: ExtractionStatus;
  provider: string;
  model: string;
  latency_ms: number;
  latency: number;
  confidence: number;
  repair_attempts: RepairAttempt[];
  repair_attempts_count: number;
  ticket_preview: string;
  original_ticket: string;
  final_json: Record<string, unknown>;
  extraction_summary: Record<string, unknown>;
}
