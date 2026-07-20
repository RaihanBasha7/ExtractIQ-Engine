/* eslint-disable @typescript-eslint/no-explicit-any */
import type {
  HealthResponse,
  MetricsResponse,
  ExtractionResult,
  HistoryItem,
  RepairAttempt,
} from '../types';

const DEFAULT_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ?? '';
const APP_START = Date.now();

function getBase(): string {
  try {
    const stored = localStorage.getItem('extractiq.apiBase');
    if (stored) return stored.replace(/\/$/, '');
  } catch { /* ignore localStorage error */ }
  return DEFAULT_BASE;
}

export function setApiBase(url: string) {
  try {
    if (url) localStorage.setItem('extractiq.apiBase', url.replace(/\/$/, ''));
    else localStorage.removeItem('extractiq.apiBase');
  } catch { /* ignore localStorage error */ }
}

export function getApiBase(): string {
  return getBase();
}

async function http<T>(path: string, init?: RequestInit, timeoutMs = 120000): Promise<T> {
  const base = getBase();
  const url = base ? `${base}${path}` : path;
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  let res: Response;
  try {
    res = await fetch(url, {
      ...init,
      signal: ctrl.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers ?? {}),
      },
    });
    clearTimeout(t);
  } catch (err) {
    clearTimeout(t);
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new Error('Request timed out');
    }
    console.error('[http] fetch failed:', err);
    throw new Error('Backend unavailable');
  }
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const msg = body?.message || body?.detail || `Request failed (${res.status})`;
    throw new Error(msg);
  }
  return body as T;
}

function num(v: unknown, d = 0): number {
  const n = typeof v === 'number' ? v : parseFloat(String(v));
  return Number.isFinite(n) ? n : d;
}

function str(v: unknown, d = ''): string {
  return typeof v === 'string' ? v : v == null ? d : String(v);
}

function obj(v: unknown): Record<string, unknown> {
  return v && typeof v === 'object' && !Array.isArray(v)
    ? (v as Record<string, unknown>)
    : {};
}

function repairAttempts(v: unknown): RepairAttempt[] {
  if (!Array.isArray(v)) return [];
  return v.map((r) => ({
    attempt: num((r as any)?.attempt, 1),
    status: (r as any)?.status === 'success' ? ('success' as const) : ('failed' as const),
    error: (r as any)?.error ?? null,
  }));
}

function healthState(s: string): HealthResponse['status'] {
  if (s === 'ok' || s === 'healthy') return 'healthy';
  if (s === 'degraded' || s === 'warning') return 'degraded';
  if (s === 'offline') return 'offline';
  return 'unknown';
}

export function normalizeExtraction(raw: unknown, ticket?: string): ExtractionResult {
  const r = obj(raw);
  const ticketText = str(r.ticket ?? r.input ?? r.raw_ticket, ticket ?? '');
  const attempts = repairAttempts(r.repair_attempts ?? r.repairs ?? r.repair_history);
  return {
    id: str(r.id ?? r.request_id ?? r.ticket_id, 'ext_' + Math.random().toString(36).slice(2, 10)),
    ticket: ticketText,
    cleaned_text: str(r.cleaned_text, ticketText.trim()),
    structured_extraction: obj(r.structured_extraction ?? r.extraction ?? r.structured ?? r.data),
    final_json: obj(r.final_json ?? r.output ?? r.result ?? r.structured_extraction ?? r.data),
    repair_attempts: attempts,
    metadata: {
      provider: str(r.provider ?? (r.metadata as any)?.provider ?? '-'),
      model: str(r.model ?? (r.metadata as any)?.model ?? '-'),
      latency_ms: num(r.latency_ms ?? (r.metadata as any)?.latency_ms ?? num(r.latency_seconds, 0) * 1000, 0),
      confidence: num(r.confidence ?? (r.metadata as any)?.confidence, 0),
      timestamp: str(r.timestamp ?? (r.metadata as any)?.timestamp ?? r.created_at, new Date().toISOString()),
      repair_attempts: num(r.retry_count ?? (r.metadata as any)?.repair_attempts ?? attempts.length, 0),
    },
    status: r.success === false ? 'failure' : 'completed',
  };
}

function normalizeHealth(raw: unknown): HealthResponse {
  const r = obj(raw);
  const checks = obj(r.checks);
  const apiCheck = obj(checks.api);
  const dbCheck = obj(checks.database);
  const llmCheck = obj(checks.llm_provider);
  const diskCheck = obj(checks.disk);
  return {
    status: healthState(str(r.status, 'unknown')),
    components: {
      api: healthState(str(apiCheck.status, 'unknown')),
      database: healthState(str(dbCheck.status, 'unknown')),
      disk: healthState(str(diskCheck.status, 'unknown')),
      llm_provider: healthState(str(llmCheck.status, 'unknown')),
    },
    timestamp: str(r.timestamp, new Date().toISOString()),
    uptime_seconds: Math.floor((Date.now() - APP_START) / 1000),
  };
}

function normalizeMetrics(raw: unknown): MetricsResponse {
  const r = obj(raw);
  const total = num(r.total_requests, 0);
  const successful = num(r.successful_extractions, 0);

  const fbRaw = obj(r.failure_breakdown);
  const failure_breakdown = Object.entries(fbRaw).map(([reason, count]) => ({
    reason,
    count: num(count, 0),
  }));

  const schemaRate = num(r.schema_valid_rate, 0);
  const repairRate = total > 0 ? (successful / total) * 100 : 100;
  const avgLatencyMs = num(r.average_processing_time, 0) * 1000;
  const avgRetries = num(r.average_retry_count, 0);

  const latencyHistory = (r.latency_history as any[]) ?? [];
  const successHistory = (r.success_history as any[]) ?? [];
  const retryHistory = (r.retry_history as any[]) ?? [];

  return {
    total_requests: total,
    success_rate: schemaRate,
    average_latency_ms: Math.round(avgLatencyMs),
    schema_valid_pct: schemaRate,
    repair_success_rate: Math.round(repairRate * 10) / 10,
    repair_attempts: Math.round(avgRetries * total),
    failure_breakdown,
    latency_history: latencyHistory.map((h: any) => ({ t: h.t ?? '', latency: num(h.latency, 0) })),
    success_history: successHistory.map((h: any) => ({ t: h.t ?? '', rate: num(h.rate, 0) })),
    retry_history: retryHistory.map((h: any) => ({ t: h.t ?? '', retries: num(h.retries, 0) })),
  };
}

export const api = {
  health: (signal?: AbortSignal) =>
    http<any>('/health', { signal }).then(normalizeHealth),

  metrics: (signal?: AbortSignal) =>
    http<any>('/v1/metrics', { signal }).then(normalizeMetrics),

  system: (signal?: AbortSignal) =>
    http<{ health: any; metrics: any }>('/v1/system', { signal }).then((r) => ({
      health: normalizeHealth(r.health),
      metrics: normalizeMetrics(r.metrics),
    })),

  extract: async (ticket: string): Promise<ExtractionResult> => {
    const ticketId = `ticket_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    const raw = await http<any>('/v1/extract', {
      method: 'POST',
      body: JSON.stringify({ ticket_id: ticketId, raw_text: ticket }),
    });
    return normalizeExtraction(raw, ticket);
  },

  extractBatch: async (tickets: string[]): Promise<ExtractionResult[]> => {
    const body = {
      tickets: tickets.map((t, i) => ({
        ticket_id: `batch_${Date.now()}_${i}_${Math.random().toString(36).slice(2, 8)}`,
        raw_text: t,
      })),
    };
    const raw = await http<{ results: any[] }>('/v1/extract/batch', {
      method: 'POST',
      body: JSON.stringify(body),
    });
    return (raw.results ?? []).map((r, i) => normalizeExtraction(r, tickets[i]));
  },

  history: async (limit = 50, offset = 0): Promise<{ items: HistoryItem[]; total: number }> => {
    const raw = await http<any>(`/v1/history?limit=${limit}&offset=${offset}`);
    const items: HistoryItem[] = (raw.items ?? []).map((r: any) => {
      const isDone = r.status === 'completed';
      return {
        id: r.request_id ?? r.ticket_id,
        request_id: r.request_id ?? '',
        ticket_id: r.ticket_id ?? '',
        timestamp: r.timestamp ?? '',
        status: isDone ? 'completed' : 'failure',
        provider: r.provider ?? '-',
        model: r.model ?? '-',
        latency_ms: Math.round(num(r.latency, 0) * 1000),
        latency: num(r.latency, 0),
        confidence: num(r.confidence, 0),
        repair_attempts: repairAttempts(r.repair_attempts),
        repair_attempts_count: Array.isArray(r.repair_attempts) ? r.repair_attempts.length : 0,
        ticket_preview: (r.original_ticket ?? '').slice(0, 200),
        original_ticket: r.original_ticket ?? '',
        final_json: obj(r.extraction_summary),
        extraction_summary: obj(r.extraction_summary),
      };
    });
    return { items, total: raw.total ?? items.length };
  },
};
