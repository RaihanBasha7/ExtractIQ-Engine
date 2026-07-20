import { memo } from 'react';

const PARTICLES = Array.from({ length: 28 }, () => ({
  x: Math.random() * 100,
  y: Math.random() * 100,
  size: Math.random() * 2 + 0.6,
  duration: Math.random() * 14 + 12,
  delay: Math.random() * 8,
  color: ['#3B82F6', '#06B6D4', '#22C55E'][Math.floor(Math.random() * 3)],
}));

export const AnimatedBackground = memo(function AnimatedBackground() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden bg-ink-950">
      <div className="absolute inset-0 bg-mesh opacity-80" />
      <div
        className="absolute inset-0 opacity-[0.18]"
        style={{
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
          maskImage:
            'radial-gradient(ellipse at 50% 0%, black 30%, transparent 80%)',
          WebkitMaskImage:
            'radial-gradient(ellipse at 50% 0%, black 30%, transparent 80%)',
        }}
      />
      <div className="absolute -top-40 left-1/4 w-[520px] h-[520px] rounded-full blur-[120px] bg-brand-blue/20 animate-blob" />
      <div className="absolute top-1/3 -right-32 w-[460px] h-[460px] rounded-full blur-[120px] bg-brand-cyan/15 animate-blob2" />
      <div className="absolute bottom-0 left-1/3 w-[420px] h-[420px] rounded-full blur-[120px] bg-brand-green/10 animate-blob3" />
      {PARTICLES.map((p, i) => (
        <span
          key={i}
          className="absolute rounded-full"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
            background: p.color,
            boxShadow: `0 0 8px ${p.color}`,
            animation: `floatParticle ${p.duration}s ${p.delay}s infinite`,
          }}
        />
      ))}
    </div>
  );
});
