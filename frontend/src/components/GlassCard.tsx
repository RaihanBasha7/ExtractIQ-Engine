import { memo, type ReactNode } from 'react';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  glow?: 'blue' | 'cyan' | 'green' | 'yellow' | 'red' | 'none';
}

export const GlassCard = memo(function GlassCard({
  children,
  className = '',
  hover = true,
  glow = 'none',
}: GlassCardProps) {
  const glowClass =
    glow === 'blue'
      ? 'hover:shadow-glow'
      : glow === 'cyan'
        ? 'hover:shadow-glow-cyan'
        : glow === 'green'
          ? 'hover:shadow-glow-green'
          : glow === 'yellow'
            ? 'hover:shadow-glow-yellow'
            : glow === 'red'
              ? 'hover:shadow-glow-red'
              : '';

  return (
    <div
      className={`glass-card animate-in ${hover ? 'glass-hover' : ''} ${glowClass} ${className}`}
    >
      {children}
    </div>
  );
});
