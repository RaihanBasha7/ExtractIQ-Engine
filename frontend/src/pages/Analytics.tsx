import { useQuery } from '@tanstack/react-query';
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts';
import { GlassCard } from '../components/GlassCard';
import { SkeletonCard } from '../components/Skeleton';
import { ErrorCard } from '../components/ErrorCard';
import { api } from '../lib/api';
import { AnimatedNumber } from '../components/AnimatedNumber';
import { AlertCircle, TrendingUp, BarChart3, Activity, Clock, ShieldCheck, Gauge, AlertTriangle } from 'lucide-react';

const FAILURE_CATEGORY_COLORS: Record<string, string> = {
  Validation: '#3B82F6',
  Provider: '#ef4444',
  Infrastructure: '#f59e0b',
  Retry: '#8b5cf6',
  Timeout: '#ec4899',
  Schema: '#06B6D4',
};


const CHART_PROPS = { isAnimationActive: false };

function normalizeFailureReason(reason: string): string {
  const r = reason.toLowerCase();
  if (r.includes('validation') || r.includes('schema') || r.includes('enum') || r.includes('field')) return 'Schema';
  if (r.includes('rate_limit') || r.includes('rate')) return 'Retry';
  if (r.includes('timeout')) return 'Timeout';
  if (r.includes('provider') || r.includes('api_error') || r.includes('model')) return 'Provider';
  if (r.includes('infrastructure')) return 'Infrastructure';
  if (r.includes('empty') || r.includes('authentication')) return 'Validation';
  return 'Provider';
}

function smoothData(data: { t: string; latency?: number; rate?: number }[], key: 'latency' | 'rate', window = 3) {
  if (!data || data.length < window) return data;
  return data.map((point, i) => {
    const vals = [];
    for (let j = Math.max(0, i - Math.floor(window / 2)); j <= Math.min(data.length - 1, i + Math.floor(window / 2)); j++) {
      const v = data[j][key];
      if (v !== undefined && v !== null) vals.push(v);
    }
    const avg = vals.length > 0 ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
    return { ...point, [key]: Math.round(avg * 10) / 10 };
  });
}

function limitPoints(data: unknown[], max = 30) {
  if (!data || data.length <= max) return data;
  const step = Math.ceil(data.length / max);
  return data.filter((_, i) => i % step === 0 || i === data.length - 1);
}

export function Analytics() {
  const q = useQuery({ queryKey: ['metrics'], queryFn: () => api.metrics(), refetchInterval: 30000 });

  if (q.isError) return <ErrorCard onRetry={() => q.refetch()} />;
  if (q.isLoading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonCard key={i} lines={4} />
        ))}
      </div>
    );
  }

  const data = q.data!;

  const categorizedFailures = (data.failure_breakdown ?? []).reduce<Record<string, number>>((acc, f) => {
    const cat = normalizeFailureReason(f.reason);
    acc[cat] = (acc[cat] || 0) + f.count;
    return acc;
  }, {});

  const failurePieData = Object.entries(categorizedFailures).map(([reason, count]) => ({ reason, count }));

  const hasFailures = failurePieData.length > 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">Analytics</h1>
        <p className="mt-1.5 text-sm text-white/50">
          Production telemetry across extraction, validation, and repair.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MiniStat label="Schema Valid %" value={data.schema_valid_pct} suffix="%" color="#3B82F6" icon={<ShieldCheck size={14} />} />
        <MiniStat label="Avg Confidence" value={data.average_confidence} suffix="%" color="#22C55E" icon={<Gauge size={14} />} />
        <MiniStat label="Avg Latency" value={data.average_latency_ms} suffix="ms" color="#06B6D4" icon={<Clock size={14} />} />
        <MiniStat label="Failure Rate" value={data.failure_rate} suffix="%" color="#ef4444" icon={<AlertTriangle size={14} />} />
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <GlassCard hover={false} className="p-6">
          <ChartTitle title="Latency Trend" subtitle="ms · last 24h" icon={<Clock size={14} className="text-brand-cyan" />} />
          {data.latency_history?.length ? (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={limitPoints(smoothData(data.latency_history, 'latency', 5), 30)}>
                  <defs>
                    <linearGradient id="a1" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#06B6D4" stopOpacity={0.5} />
                      <stop offset="100%" stopColor="#06B6D4" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="t" stroke="rgba(255,255,255,0.2)" fontSize={10} tickLine={false} axisLine={false} tickFormatter={(v) => {
                    if (!v) return ''; const d = new Date(v); return isNaN(d.getTime()) ? v : `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
                  }} />
                  <YAxis stroke="rgba(255,255,255,0.2)" fontSize={10} tickLine={false} axisLine={false} width={50} tickFormatter={(v) => v >= 1000 ? `${(v / 1000).toFixed(1)}s` : `${v}ms`} />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    labelFormatter={(v) => { const d = new Date(v); return isNaN(d.getTime()) ? v : d.toLocaleString(); }}
                    formatter={(v: number) => [v >= 1000 ? `${(v / 1000).toFixed(2)}s` : `${Math.round(v)}ms`, 'Latency']}
                  />
                  <Area type="monotone" dataKey="latency" stroke="#06B6D4" strokeWidth={2} fill="url(#a1)" dot={false} {...CHART_PROPS} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-72 flex flex-col items-center justify-center text-white/30">
              <TrendingUp size={28} className="mb-2 opacity-40" />
              <p className="text-xs">Collecting telemetry...</p>
              <p className="text-[10px] mt-1 text-white/20">No sufficient historical data yet</p>
            </div>
          )}
        </GlassCard>

        <GlassCard hover={false} className="p-6">
          <ChartTitle title="Success Rate" subtitle="% · last 24h" icon={<Activity size={14} className="text-brand-green" />} />
          {data.success_history?.length ? (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={limitPoints(smoothData(data.success_history, 'rate', 5), 30)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="t" stroke="rgba(255,255,255,0.2)" fontSize={10} tickLine={false} axisLine={false} tickFormatter={(v) => {
                    if (!v) return ''; const d = new Date(v); return isNaN(d.getTime()) ? v : `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
                  }} />
                  <YAxis domain={[0, 100]} stroke="rgba(255,255,255,0.2)" fontSize={10} tickLine={false} axisLine={false} width={40} tickFormatter={(v) => `${v}%`} />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    labelFormatter={(v) => { const d = new Date(v); return isNaN(d.getTime()) ? v : d.toLocaleString(); }}
                    formatter={(v: number) => [`${Math.round(v)}%`, 'Success Rate']}
                  />
                  <Line type="monotone" dataKey="rate" stroke="#22C55E" strokeWidth={2} dot={false} {...CHART_PROPS} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-72 flex flex-col items-center justify-center text-white/30">
              <BarChart3 size={28} className="mb-2 opacity-40" />
              <p className="text-xs">Collecting telemetry...</p>
              <p className="text-[10px] mt-1 text-white/20">No sufficient historical data yet</p>
            </div>
          )}
        </GlassCard>

        <GlassCard hover={false} className="p-6">
          <ChartTitle title="Retry Count" subtitle="per hour · last 24h" icon={<Activity size={14} className="text-brand-blue" />} />
          {data.retry_history?.length ? (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={limitPoints(data.retry_history, 30)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="t" stroke="rgba(255,255,255,0.2)" fontSize={10} tickLine={false} axisLine={false} tickFormatter={(v) => {
                    if (!v) return ''; const d = new Date(v); return isNaN(d.getTime()) ? v : `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
                  }} />
                  <YAxis stroke="rgba(255,255,255,0.2)" fontSize={10} tickLine={false} axisLine={false} width={40} />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    labelFormatter={(v) => { const d = new Date(v); return isNaN(d.getTime()) ? v : d.toLocaleString(); }}
                  />
                  <Bar dataKey="retries" fill="#3B82F6" radius={[6, 6, 0, 0]} {...CHART_PROPS} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-72 flex flex-col items-center justify-center text-white/30">
              <BarChart3 size={28} className="mb-2 opacity-40" />
              <p className="text-xs">Collecting telemetry...</p>
              <p className="text-[10px] mt-1 text-white/20">No retry data recorded yet</p>
            </div>
          )}
        </GlassCard>

        <GlassCard hover={false} className="p-6">
          <ChartTitle title="Failure Breakdown" subtitle="by category" icon={<AlertCircle size={14} className="text-red-400" />} />
          {hasFailures ? (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={failurePieData}
                    dataKey="count"
                    nameKey="reason"
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={3}
                    {...CHART_PROPS}
                  >
                    {failurePieData.map((entry) => (
                      <Cell key={entry.reason} fill={FAILURE_CATEGORY_COLORS[entry.reason] || '#6b7280'} stroke="rgba(0,0,0,0.3)" />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(v: number) => [v, 'Failures']}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex flex-wrap gap-3 justify-center mt-2">
                {failurePieData.map((f) => (
                  <div key={f.reason} className="flex items-center gap-1.5 text-xs text-white/55">
                    <span className="w-2.5 h-2.5 rounded-sm" style={{ background: FAILURE_CATEGORY_COLORS[f.reason] || '#6b7280' }} />
                    {f.reason} <span className="text-white/40">({f.count})</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="h-72 flex flex-col items-center justify-center text-white/30">
              <AlertCircle size={28} className="mb-2 opacity-40" />
              <p className="text-xs">No failures to display</p>
              <p className="text-[10px] mt-1 text-white/20">All extractions processed successfully</p>
            </div>
          )}
        </GlassCard>
      </div>

      <GlassCard hover={false} className="p-6">
        <ChartTitle title="Performance Summary" subtitle="Aggregate metrics overview" icon={<Activity size={14} className="text-brand-blue" />} />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-sm">
          <PerfStat label="Total Requests" value={data.total_requests} />
          <PerfStat label="Repair Success Rate" value={`${data.repair_success_rate}%`} />
          <PerfStat label="Needs Review Count" value={data.needs_review_count} />
          <PerfStat label="Repair Count" value={data.repair_count} />
        </div>
      </GlassCard>
    </div>
  );
}

const tooltipStyle = {
  background: 'rgba(10,14,26,0.95)',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: 12,
  fontSize: 12,
  padding: 10,
};

function ChartTitle({ title, subtitle, icon }: { title: string; subtitle: string; icon?: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      {icon}
      <div>
        <h3 className="text-base font-semibold text-white">{title}</h3>
        <p className="text-xs text-white/40">{subtitle}</p>
      </div>
    </div>
  );
}

function MiniStat({ label, value, suffix, color, icon }: { label: string; value: number; suffix: string; color: string; icon?: React.ReactNode }) {
  return (
    <GlassCard className="p-4">
      <div className="flex items-center justify-between mb-1">
        <p className="text-xs text-white/45 font-medium">{label}</p>
        {icon && <span style={{ color }}>{icon}</span>}
      </div>
      <p className="text-3xl font-bold tracking-tight" style={{ color }}>
        <AnimatedNumber value={value} suffix={suffix} decimals={1} />
      </p>
    </GlassCard>
  );
}

function PerfStat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-lg bg-white/[0.02] border border-white/[0.05] px-4 py-3">
      <p className="text-xs text-white/40">{label}</p>
      <p className="text-xl font-bold text-white mt-0.5 tabular-nums">{value}</p>
    </div>
  );
}
