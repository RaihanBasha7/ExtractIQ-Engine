import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, ChevronDown, CheckCircle2, XCircle, Clock, History as HistoryIcon, ChevronLeft, ChevronRight, AlertCircle, AlertTriangle } from 'lucide-react';
import { api } from '../lib/api';
import { GlassCard } from '../components/GlassCard';
import { JsonBlock } from '../components/JsonBlock';
import { SkeletonCard } from '../components/Skeleton';
import { ErrorCard } from '../components/ErrorCard';
import type { HistoryItem, ExtractionStatus } from '../types';

const PAGE_SIZE = 20;
const filters: { key: 'all' | ExtractionStatus; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'completed', label: 'Completed' },
  { key: 'needs_review', label: 'Needs Review' },
  { key: 'failure', label: 'Failures' },
];

export function History() {
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<'all' | ExtractionStatus>('all');
  const [expanded, setExpanded] = useState<string | null>(null);

  const q = useQuery({
    queryKey: ['history', page],
    queryFn: () => api.history(PAGE_SIZE, page * PAGE_SIZE),
  });

  const items = useMemo(() => {
    if (!q.data?.items) return [];
    return q.data.items.filter((it) => {
      if (filter !== 'all' && it.status !== filter) return false;
      if (search && !it.ticket_preview.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [q.data, search, filter]);

  const totalPages = q.data ? Math.ceil(q.data.total / PAGE_SIZE) : 0;

  if (q.isError) return <ErrorCard onRetry={() => q.refetch()} />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">History</h1>
        <p className="mt-1.5 text-sm text-white/50">Searchable timeline of every extraction.</p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 rounded-xl bg-white/[0.03] border border-white/[0.06] px-3 py-2 flex-1 min-w-[220px]">
          <Search size={14} className="text-white/40" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search tickets&hellip;"
            className="bg-transparent text-sm text-white/85 placeholder:text-white/30 outline-none w-full"
          />
        </div>
        <div className="flex gap-1.5">
          {filters.map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`chip border transition-all ${
                filter === f.key
                  ? 'bg-brand-blue/15 text-brand-blue border-brand-blue/30'
                  : 'bg-white/[0.03] text-white/55 border-white/[0.06] hover:text-white'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {q.isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <SkeletonCard key={i} lines={2} />
          ))}
        </div>
      ) : items.length === 0 ? (
        <EmptyState isSearch={!!(search || filter !== 'all')} />
      ) : (
        <div className="relative">
          <div className="absolute left-[19px] top-2 bottom-2 w-px bg-gradient-to-b from-brand-blue/40 via-brand-cyan/30 to-transparent" />
          <div className="space-y-3">
            {items.map((it, i) => (
              <HistoryRow
                key={`${it.id}-${i}`}
                item={it}
                expanded={expanded === `${it.id}-${i}`}
                onToggle={() => setExpanded((v) => (v === `${it.id}-${i}` ? null : `${it.id}-${i}`))}
              />
            ))}
          </div>
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3 pt-2">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="btn-ghost disabled:opacity-30"
          >
            <ChevronLeft size={16} /> Previous
          </button>
          <span className="text-xs text-white/40">
            Page {page + 1} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="btn-ghost disabled:opacity-30"
          >
            Next <ChevronRight size={16} />
          </button>
        </div>
      )}
    </div>
  );
}

function HistoryRow({
  item,
  expanded,
  onToggle,
}: {
  item: HistoryItem;
  expanded: boolean;
  onToggle: () => void;
}) {
  const fs = item.final_status;
  const statusColor = fs === 'SUCCESS' ? 'bg-brand-green/15 border-brand-green/40 text-brand-green' :
    fs === 'REPAIRED' ? 'bg-yellow-500/15 border-yellow-500/40 text-yellow-400' :
    'bg-red-500/15 border-red-500/40 text-red-400';
  const statusIcon = fs === 'SUCCESS' ? <CheckCircle2 size={16} /> :
    fs === 'REPAIRED' ? <AlertCircle size={16} /> :
    <XCircle size={16} />;
  return (
    <div className="relative pl-12 animate-in">
      <div className={`absolute left-0 top-4 w-10 h-10 rounded-full border-2 flex items-center justify-center ${statusColor}`}>
        {statusIcon}
      </div>
      <button onClick={onToggle} className="w-full text-left">
        <GlassCard className="p-4">
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <div className="min-w-0">
              <p className="text-sm text-white/85 truncate">{item.ticket_preview}</p>
              <div className="flex items-center gap-3 mt-1.5 text-[11px] text-white/40">
                <span className={
                  fs === 'SUCCESS' ? 'text-brand-green' :
                  fs === 'REPAIRED' ? 'text-yellow-400' :
                  'text-red-400'
                }>{fs}</span>
                <span>&middot;</span>
                <span>{new Date(item.timestamp).toLocaleString()}</span>
                <span>&middot;</span>
                <span>{item.model}</span>
                <span>&middot;</span>
                <span className="flex items-center gap-1">
                  <Clock size={10} /> {item.latency_ms}ms
                </span>
                <span>&middot;</span>
                <span>{item.confidence_score}% conf</span>
                {item.repair_attempts_count > 0 && (
                  <>
                    <span>&middot;</span>
                    <span className="text-brand-cyan">{item.repair_attempts_count} repairs</span>
                  </>
                )}
                {item.validation_status && (
                  <>
                    <span>&middot;</span>
                    <span className={item.validation_status === 'passed' ? 'text-brand-green' : 'text-red-400'}>
                      {item.validation_status === 'passed' ? 'Valid' : 'Invalid'}
                    </span>
                  </>
                )}
              </div>
              {item.needs_review_reason && (
                <p className="text-[10px] text-yellow-400/70 mt-1">{item.needs_review_reason}</p>
              )}
            </div>
            <ChevronDown
              size={16}
              className={`text-white/40 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
            />
          </div>
          <div
            className={`overflow-hidden transition-all duration-300 ease-out ${
              expanded ? 'max-h-[600px] opacity-100 mt-4' : 'max-h-0 opacity-0'
            }`}
          >
            <div className="space-y-3">
              <JsonBlock data={item.final_json} maxHeight="320px" />
              {item.repair_attempts.length > 0 && (
                <RepairTimeline attempts={item.repair_attempts} />
              )}
            </div>
          </div>
        </GlassCard>
      </button>
    </div>
  );
}

function RepairTimeline({ attempts }: { attempts: { attempt: number; status: string; error: string | null }[] }) {
  return (
    <div className="rounded-xl bg-[#0a0e1a] border border-white/[0.05] p-3">
      <p className="text-xs font-semibold text-white/60 mb-2 flex items-center gap-1.5">
        <AlertCircle size={11} /> Repair Attempts
      </p>
      <div className="space-y-1.5">
        {attempts.map((a) => (
          <div key={a.attempt} className="flex items-center gap-2 text-xs">
            <div
              className={`w-5 h-5 rounded-full flex items-center justify-center ${
                a.status === 'success'
                  ? 'bg-brand-green/15 text-brand-green'
                  : 'bg-yellow-500/15 text-yellow-400'
              }`}
            >
              {a.status === 'success' ? (
                <CheckCircle2 size={10} />
              ) : (
                <XCircle size={10} />
              )}
            </div>
            <span className="text-white/50 min-w-[60px]">#{a.attempt}</span>
            <span className={a.status === 'success' ? 'text-brand-green' : 'text-yellow-400'}>
              {a.status === 'success' ? 'Success' : a.error ?? 'Failed'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function EmptyState({ isSearch }: { isSearch?: boolean }) {
  return (
    <div className="glass-card p-12 flex flex-col items-center text-center">
      <div className="w-14 h-14 rounded-2xl bg-white/[0.04] border border-white/[0.06] flex items-center justify-center mb-4">
        {isSearch ? <Search size={22} className="text-white/30" /> : <HistoryIcon size={22} className="text-white/30" />}
      </div>
      <p className="text-sm text-white/50">
        {isSearch ? 'No extractions match your search.' : 'No extraction history yet.'}
      </p>
      <p className="text-xs text-white/35 mt-1">
        {isSearch ? 'Try adjusting your filter or search term.' : 'Run an extraction to see it appear here.'}
      </p>
    </div>
  );
}
