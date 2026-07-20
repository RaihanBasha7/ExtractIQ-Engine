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
import { AlertCircle, TrendingUp, BarChart3 } from 'lucide-react';

const PIE_COLORS = ['#3B82F6', '#06B6D4', '#22C55E', '#f59e0b', '#ef4444'];
const CHART_PROPS = { isAnimationActive: false };

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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">Analytics</h1>
        <p className="mt-1.5 text-sm text-white/50">
          Production telemetry across extraction, validation, and repair.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MiniStat label="Success Rate" value={data.success_rate} suffix="%" color="#22C55E" />
        <MiniStat label="Avg Latency" value={data.average_latency_ms} suffix="ms" color="#06B6D4" />
        <MiniStat label="Schema Valid" value={data.schema_valid_pct} suffix="%" color="#3B82F6" />
        <MiniStat label="Repair Success" value={data.repair_success_rate} suffix="%" color="#22C55E" />
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <GlassCard hover={false} className="p-6">
          <ChartTitle title="Latency Trend" subtitle="ms · last 24h" />
          {data.latency_history?.length ? (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.latency_history}>
                  <defs>
                    <linearGradient id="a1" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#06B6D4" stopOpacity={0.5} />
                      <stop offset="100%" stopColor="#06B6D4" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="t" stroke="rgba(255,255,255,0.2)" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis stroke="rgba(255,255,255,0.2)" fontSize={10} tickLine={false} axisLine={false} width={40} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Area type="monotone" dataKey="latency" stroke="#06B6D4" strokeWidth={2} fill="url(#a1)" {...CHART_PROPS} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-72 flex flex-col items-center justify-center text-white/30">
              <TrendingUp size={28} className="mb-2 opacity-40" />
              <p className="text-xs">Run extractions to see latency data</p>
            </div>
          )}
        </GlassCard>

        <GlassCard hover={false} className="p-6">
          <ChartTitle title="Success Rate" subtitle="% · last 24h" />
          {data.success_history?.length ? (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.success_history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="t" stroke="rgba(255,255,255,0.2)" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis domain={[80, 100]} stroke="rgba(255,255,255,0.2)" fontSize={10} tickLine={false} axisLine={false} width={40} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Line type="monotone" dataKey="rate" stroke="#22C55E" strokeWidth={2} dot={false} {...CHART_PROPS} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-72 flex flex-col items-center justify-center text-white/30">
              <BarChart3 size={28} className="mb-2 opacity-40" />
              <p className="text-xs">Run extractions to see success rate</p>
            </div>
          )}
        </GlassCard>

        <GlassCard hover={false} className="p-6">
          <ChartTitle title="Retry Count" subtitle="per hour · last 24h" />
          {data.retry_history?.length ? (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.retry_history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="t" stroke="rgba(255,255,255,0.2)" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis stroke="rgba(255,255,255,0.2)" fontSize={10} tickLine={false} axisLine={false} width={40} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Bar dataKey="retries" fill="#3B82F6" radius={[6, 6, 0, 0]} {...CHART_PROPS} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-72 flex flex-col items-center justify-center text-white/30">
              <BarChart3 size={28} className="mb-2 opacity-40" />
              <p className="text-xs">Run extractions to see retry data</p>
            </div>
          )}
        </GlassCard>

        <GlassCard hover={false} className="p-6">
          <ChartTitle title="Failure Breakdown" subtitle="by reason" />
          {data.failure_breakdown?.length ? (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.failure_breakdown}
                    dataKey="count"
                    nameKey="reason"
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={95}
                    paddingAngle={3}
                    {...CHART_PROPS}
                  >
                    {data.failure_breakdown.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} stroke="rgba(0,0,0,0.3)" />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={tooltipStyle} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-72 flex flex-col items-center justify-center text-white/30">
              <AlertCircle size={28} className="mb-2 opacity-40" />
              <p className="text-xs">No failures to display</p>
            </div>
          )}
          {data.failure_breakdown?.length ? (
            <div className="flex flex-wrap gap-3 justify-center mt-2">
              {data.failure_breakdown.map((f, i) => (
                <div key={f.reason} className="flex items-center gap-1.5 text-xs text-white/55">
                  <span className="w-2.5 h-2.5 rounded-sm" style={{ background: PIE_COLORS[i % PIE_COLORS.length] }} />
                  {f.reason}
                </div>
              ))}
            </div>
          ) : null}
        </GlassCard>
      </div>
    </div>
  );
}

const tooltipStyle = {
  background: 'rgba(10,14,26,0.95)',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: 12,
  fontSize: 12,
};

function ChartTitle({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="mb-4">
      <h3 className="text-base font-semibold text-white">{title}</h3>
      <p className="text-xs text-white/40">{subtitle}</p>
    </div>
  );
}

function MiniStat({ label, value, suffix, color }: { label: string; value: number; suffix: string; color: string }) {
  return (
    <GlassCard className="p-5">
      <p className="text-3xl font-bold tracking-tight" style={{ color }}>
        <AnimatedNumber value={value} suffix={suffix} decimals={1} />
      </p>
      <p className="mt-1 text-xs text-white/45 font-medium">{label}</p>
    </GlassCard>
  );
}
