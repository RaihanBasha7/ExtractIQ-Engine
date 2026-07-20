import type { HealthState } from '../types';

interface StatusDotProps {
  state: HealthState;
  size?: number;
  pulse?: boolean;
}

const colorMap: Record<HealthState, string> = {
  healthy: 'bg-brand-green',
  warning: 'bg-yellow-400',
  degraded: 'bg-red-500',
  offline: 'bg-red-500',
  unknown: 'bg-white/30',
};

const ringMap: Record<HealthState, string> = {
  healthy: 'bg-brand-green/30',
  warning: 'bg-yellow-400/30',
  degraded: 'bg-red-500/30',
  offline: 'bg-red-500/30',
  unknown: 'bg-white/10',
};

export function StatusDot({ state, size = 10, pulse = true }: StatusDotProps) {
  return (
    <span className="relative inline-flex" style={{ width: size, height: size }}>
      {pulse && (
        <span
          className={`absolute inset-0 rounded-full ${ringMap[state]} animate-ping`}
          style={{ animationDuration: '2s' }}
        />
      )}
      <span className={`relative inline-flex rounded-full ${colorMap[state]}`} style={{ width: size, height: size }} />
    </span>
  );
}
