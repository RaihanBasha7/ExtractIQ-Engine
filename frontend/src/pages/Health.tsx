import { useQuery } from '@tanstack/react-query';
import {
  Server,
  Database,
  HardDrive,
  BrainCircuit,
  Activity,
  RefreshCw,
} from 'lucide-react';
import { api } from '../lib/api';
import { GlassCard } from '../components/GlassCard';
import { StatusDot } from '../components/StatusDot';
import { SkeletonCard } from '../components/Skeleton';
import { ErrorCard } from '../components/ErrorCard';
import type { HealthState } from '../types';

const components = [
  { key: 'api', label: 'API', icon: Server, desc: 'REST + WebSocket gateway' },
  { key: 'database', label: 'Database', icon: Database, desc: 'Postgres primary' },
  { key: 'disk', label: 'Disk', icon: HardDrive, desc: 'Object storage' },
  { key: 'llm_provider', label: 'LLM Provider', icon: BrainCircuit, desc: 'OpenAI gateway' },
] as const;

const stateColor: Record<HealthState, { text: string; bg: string; border: string; label: string }> = {
  healthy: { text: 'text-brand-green', bg: 'bg-brand-green/10', border: 'border-brand-green/30', label: 'Healthy' },
  warning: { text: 'text-yellow-400', bg: 'bg-yellow-400/10', border: 'border-yellow-400/30', label: 'Degraded' },
  degraded: { text: 'text-yellow-400', bg: 'bg-yellow-400/10', border: 'border-yellow-400/30', label: 'Degraded' },
  offline: { text: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30', label: 'Offline' },
  unknown: { text: 'text-white/50', bg: 'bg-white/[0.04]', border: 'border-white/[0.08]', label: 'Unknown' },
};

export function Health() {
  const q = useQuery({ queryKey: ['health'], queryFn: () => api.health(), refetchInterval: 15000 });

  if (q.isError) return <ErrorCard onRetry={() => q.refetch()} />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Health</h1>
          <p className="mt-1.5 text-sm text-white/50">Live status of every system component.</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="chip bg-white/[0.04] border border-white/[0.08] text-white/60">
            <Activity size={12} className="text-brand-cyan" /> auto-refresh 15s
          </span>
          <button onClick={() => q.refetch()} className="btn-ghost" aria-label="Refresh health">
            <RefreshCw size={14} className={q.isFetching ? 'animate-spin' : ''} /> Refresh
          </button>
        </div>
      </div>

      {!q.isLoading && (
        <GlassCard hover={false} className="p-6 flex items-center gap-4">
          <StatusDot state={q.data?.status ?? 'unknown'} size={14} />
          <div>
            <p className="text-lg font-semibold text-white">
              System status:{' '}
              <span className={stateColor[q.data?.status ?? 'unknown'].text}>
                {stateColor[q.data?.status ?? 'unknown'].label}
              </span>
            </p>
            <p className="text-xs text-white/45">
              Uptime {Math.floor((q.data?.uptime_seconds ?? 0) / 3600)}h{' '}
              {Math.floor(((q.data?.uptime_seconds ?? 0) % 3600) / 60)}m · last check{' '}
              {q.data ? new Date(q.data.timestamp).toLocaleTimeString() : '—'}
            </p>
          </div>
        </GlassCard>
      )}

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {q.isLoading
          ? Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} lines={3} />)
          : components.map((c) => {
              const state = q.data?.components[c.key] ?? 'unknown';
              const s = stateColor[state];
              return (
                <GlassCard key={c.key} className="p-5 relative overflow-hidden" hover={false}>
                  <div className="absolute -top-10 -right-10 w-32 h-32 rounded-full blur-2xl bg-white/[0.04]" />
                  <div className="relative">
                    <div className="flex items-center justify-between">
                      <div className={`w-11 h-11 rounded-xl ${s.bg} ${s.border} border flex items-center justify-center ${s.text}`}>
                        <c.icon size={20} />
                      </div>
                      <StatusDot state={state} size={9} />
                    </div>
                    <p className="mt-4 text-base font-semibold text-white">{c.label}</p>
                    <p className="text-xs text-white/40 mt-0.5">{c.desc}</p>
                    <p className={`mt-3 text-sm font-medium ${s.text}`}>
                      {s.label}
                    </p>
                  </div>
                </GlassCard>
              );
            })}
      </div>
    </div>
  );
}
