import type { ReactNode } from 'react';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  glow?: 'blue' | 'cyan' | 'green' | 'none';
}

export function GlassCard({
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
          : '';

  return (
    <div
      className={`glass-card animate-in ${hover ? 'glass-hover' : ''} ${glowClass} ${className}`}
    >
      {children}
    </div>
  );
}
