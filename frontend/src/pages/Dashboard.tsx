/* eslint-disable @typescript-eslint/no-explicit-any */
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  CheckCircle2,
  Clock,
  Gauge,
  Recycle,
  ShieldCheck,
  ArrowUpRight,
  Sparkles,
  AlertCircle,
  BarChart3,
  TrendingUp,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  BarChart,
  Bar,
} from 'recharts';
import { api } from '../lib/api';
import { GlassCard } from '../components/GlassCard';
import { AnimatedNumber } from '../components/AnimatedNumber';
import { WorkflowStrip } from '../components/WorkflowStrip';
import { StatusDot } from '../components/StatusDot';
import { SkeletonCard } from '../components/Skeleton';
import { ErrorCard } from '../components/ErrorCard';
import { ParticleField } from '../components/ParticleField';

const CHART_PROPS = { isAnimationActive: false };

const stats = [
  { key: 'total_requests', label: 'Total Requests', icon: Activity, color: 'text-brand-blue', glow: 'blue' as const, suffix: '', decimals: 0 },
  { key: 'success_rate', label: 'Success Rate', icon: CheckCircle2, color: 'text-brand-green', glow: 'green' as const, suffix: '%', decimals: 1 },
  { key: 'average_latency_ms', label: 'Avg Latency', icon: Clock, color: 'text-brand-cyan', glow: 'cyan' as const, suffix: 'ms', decimals: 0 },
  { key: 'schema_valid_pct', label: 'Schema Valid', icon: ShieldCheck, color: 'text-brand-blue', glow: 'blue' as const, suffix: '%', decimals: 1 },
  { key: 'repair_success_rate', label: 'Repair Success', icon: Recycle, color: 'text-brand-green', glow: 'green' as const, suffix: '%', decimals: 1 },
];

const tooltipStyle = {
  background: 'rgba(10,14,26,0.95)',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: 12,
  fontSize: 12,
};

export function Dashboard() {
  const sysQ = useQuery({
    queryKey: ['system'],
    queryFn: () => api.system(),
    refetchInterval: 30000,
  });

  if (sysQ.isError) return <ErrorCard onRetry={() => sysQ.refetch()} />;

  const metricsData = sysQ.data?.metrics;
  const healthData = sysQ.data?.health;

  return (
    <div className="relative space-y-8">
      <div className="absolute inset-0 -z-[1] overflow-hidden rounded-2xl pointer-events-none">
        <ParticleField count={270} />
      </div>

      <section className="relative pt-8 pb-4 text-center">
        <div className="inline-flex items-center gap-2 chip bg-white/[0.04] border border-white/[0.08] text-white/60 mb-6">
          <Sparkles size={12} className="text-brand-cyan" />
          Production-grade structured extraction
        </div>
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight">
          <span className="text-gradient">ExtractIQ</span>{' '}
          <span className="text-white">Engine</span>
        </h1>
        <p className="mt-5 text-lg text-white/55 max-w-2xl mx-auto leading-relaxed">
          AI-powered structured extraction with automatic schema repair and
          production-grade reliability.
        </p>

        <div className="mt-10">
          <WorkflowStrip />
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <div className="glass rounded-full px-4 py-2 flex items-center gap-2 text-sm">
            <StatusDot state={healthData?.status ?? 'unknown'} size={8} />
            <span className="text-white/70">Health: {healthData?.status ?? 'checking'}</span>
          </div>
          <div className="glass rounded-full px-4 py-2 flex items-center gap-2 text-sm text-white/70">
            <Gauge size={13} className="text-brand-cyan" />
            Uptime {Math.round((healthData?.uptime_seconds ?? 0) / 3600)}h
          </div>
        </div>
      </section>

      <section>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {sysQ.isLoading
            ? Array.from({ length: 5 }).map((_, i) => <SkeletonCard key={i} lines={2} />)
            : stats.map((s) => (
                <GlassCard key={s.key} glow={s.glow} className="p-5 group">
                  <div className="flex items-center justify-between">
                    <div className={`w-10 h-10 rounded-xl bg-white/[0.04] border border-white/[0.06] flex items-center justify-center ${s.color}`}>
                      <s.icon size={18} />
                    </div>
                    <ArrowUpRight size={15} className="text-white/20 group-hover:text-white/60 transition-colors" />
                  </div>
                  <p className="mt-4 text-3xl font-bold text-white tracking-tight tabular-nums">
                    <AnimatedNumber
                      value={(metricsData as any)?.[s.key] ?? 0}
                      suffix={s.suffix}
                      decimals={s.decimals}
                    />
                  </p>
                  <p className="mt-1 text-xs text-white/45 font-medium">{s.label}</p>
                </GlassCard>
              ))}
        </div>
      </section>

      <section className="grid lg:grid-cols-2 gap-4">
        <GlassCard className="p-6" hover={false}>
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-base font-semibold text-white">Latency</h3>
              <p className="text-xs text-white/40">Per extraction · ms</p>
            </div>
            <span className="chip bg-brand-cyan/10 text-brand-cyan border border-brand-cyan/20">live</span>
          </div>
          <div className="h-64">
            {metricsData?.latency_history?.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={metricsData.latency_history}>
                  <defs>
                    <linearGradient id="lat" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#06B6D4" stopOpacity={0.5} />
                      <stop offset="100%" stopColor="#06B6D4" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="t" stroke="rgba(255,255,255,0.2)" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis stroke="rgba(255,255,255,0.2)" fontSize={10} tickLine={false} axisLine={false} width={40} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Area type="monotone" dataKey="latency" stroke="#06B6D4" strokeWidth={2} fill="url(#lat)" {...CHART_PROPS} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-white/30">
                <TrendingUp size={28} className="mb-2 opacity-40" />
                <p className="text-xs">Run extractions to see latency trend</p>
              </div>
            )}
          </div>
        </GlassCard>

        <GlassCard className="p-6" hover={false}>
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-base font-semibold text-white">Success Rate</h3>
              <p className="text-xs text-white/40">Per extraction · %</p>
            </div>
            <span className="chip bg-brand-green/10 text-brand-green border border-brand-green/20">live</span>
          </div>
          <div className="h-64">
            {metricsData?.success_history?.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={metricsData.success_history}>
                  <defs>
                    <linearGradient id="succ" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#22C55E" stopOpacity={0.5} />
                      <stop offset="100%" stopColor="#22C55E" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="t" stroke="rgba(255,255,255,0.2)" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis domain={[80, 100]} stroke="rgba(255,255,255,0.2)" fontSize={10} tickLine={false} axisLine={false} width={40} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Area type="monotone" dataKey="rate" stroke="#22C55E" strokeWidth={2} fill="url(#succ)" {...CHART_PROPS} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-white/30">
                <BarChart3 size={28} className="mb-2 opacity-40" />
                <p className="text-xs">Run extractions to see success trend</p>
              </div>
            )}
          </div>
        </GlassCard>
      </section>

      <section>
        <GlassCard className="p-6" hover={false}>
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-base font-semibold text-white">Failure Breakdown</h3>
              <p className="text-xs text-white/40">Reasons across all requests</p>
            </div>
          </div>
          {metricsData?.failure_breakdown?.length ? (
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={metricsData.failure_breakdown} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false} />
                  <XAxis type="number" stroke="rgba(255,255,255,0.2)" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis type="category" dataKey="reason" stroke="rgba(255,255,255,0.4)" fontSize={10} tickLine={false} axisLine={false} width={130} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Bar dataKey="count" fill="#3B82F6" radius={[0, 8, 8, 0]} {...CHART_PROPS} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-56 flex flex-col items-center justify-center text-white/30">
              <AlertCircle size={24} className="mb-2 opacity-40" />
              <p className="text-xs">No failures recorded</p>
            </div>
          )}
        </GlassCard>
      </section>
    </div>
  );
}
