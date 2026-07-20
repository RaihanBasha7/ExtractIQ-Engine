import { useEffect, useRef } from 'react';

interface ParticleFieldProps {
  count?: number;
  className?: string;
}

type Layer = 'back' | 'mid' | 'front';

interface P {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  alpha: number;
  baseAlpha: number;
  phase: number;
  phaseSpeed: number;
  wobble: number;
  wobbleAmp: number;
  color: string;
  glow: number;
  layer: Layer;
}

const COLORS = ['#06B6D4', '#3B82F6', '#22C55E', '#0EA5E9', '#67E8F9', '#A78BFA', '#E6EDF6'];

const LAYER_WEIGHT: Record<Layer, number> = { back: 0.35, mid: 0.65, front: 1 };

function pickLayer(): Layer {
  const r = Math.random();
  if (r < 0.4) return 'back';
  if (r < 0.8) return 'mid';
  return 'front';
}

function pickSize(): number {
  const r = Math.random();
  if (r < 0.5) return 1 + Math.random() * 1;
  if (r < 0.8) return 2.5 + Math.random() * 1.5;
  if (r < 0.95) return 4.5 + Math.random() * 2;
  return 7 + Math.random() * 3;
}

export function ParticleField({ count = 270, className = '' }: ParticleFieldProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce) return;

    let raf = 0;
    let running = true;
    let dpr = Math.min(window.devicePixelRatio || 1, 2);
    let w = 0;
    let h = 0;
    let particles: P[] = [];
    const mouse = { x: -9999, y: -9999, active: false };

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      w = rect.width;
      h = rect.height;
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const spawn = (p: P, atBottom = false) => {
      p.x = Math.random() * w;
      p.y = atBottom ? h + Math.random() * 60 : Math.random() * h;
      p.phase = Math.random() * Math.PI * 2;
      p.phaseSpeed = 0.004 + Math.random() * 0.01;
      p.wobbleAmp = 0.3 + Math.random() * 0.8;
    };

    const seed = () => {
      particles = Array.from({ length: count }, () => {
        const layer = pickLayer();
        const weight = LAYER_WEIGHT[layer];
        const size = pickSize();
        const p: P = {
          x: 0, y: 0,
          vx: (Math.random() - 0.5) * 0.06 * weight,
          vy: -(0.04 + Math.random() * 0.2) * weight,
          size: size * (layer === 'back' ? 0.8 : layer === 'mid' ? 1 : 1.15),
          alpha: 0,
          baseAlpha: 0.15 + Math.random() * 0.5,
          phase: 0, phaseSpeed: 0.01, wobble: 0.1, wobbleAmp: 0.5,
          color: COLORS[Math.floor(Math.random() * COLORS.length)],
          glow: size > 4 ? 6 + Math.random() * 10 : 2 + Math.random() * 4,
          layer,
        };
        spawn(p);
        p.alpha = p.baseAlpha * Math.random();
        return p;
      });
    };

    const step = () => {
      if (!running) return;
      ctx.clearRect(0, 0, w, h);

      for (const p of particles) {
        p.phase += p.phaseSpeed;
        p.x += p.vx + Math.sin(p.phase * 1.7) * p.wobbleAmp * 0.04;
        p.y += p.vy;

        if (mouse.active) {
          const dx = p.x - mouse.x;
          const dy = p.y - mouse.y;
          const dist2 = dx * dx + dy * dy;
          const R = 100;
          if (dist2 < R * R && dist2 > 0.01) {
            const dist = Math.sqrt(dist2);
            const force = (1 - dist / R) * 0.5 * LAYER_WEIGHT[p.layer];
            p.x += (dx / dist) * force;
            p.y += (dy / dist) * force;
          }
        }

        const pulse = 0.5 + 0.5 * Math.sin(p.phase * 1.3);
        p.alpha = p.baseAlpha * (0.5 + 0.5 * pulse);

        if (p.y < -16) { spawn(p, true); p.alpha = 0; }
        if (p.x < -16) p.x = w + 14;
        if (p.x > w + 16) p.x = -14;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = Math.min(p.alpha, 0.9);
        ctx.shadowColor = p.color;
        ctx.shadowBlur = p.glow;
        ctx.fill();
      }
      ctx.globalAlpha = 1;
      ctx.shadowBlur = 0;
      raf = requestAnimationFrame(step);
    };

    const onVisibility = () => {
      running = !document.hidden;
      if (running) raf = requestAnimationFrame(step);
      else cancelAnimationFrame(raf);
    };

    const onMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
      mouse.active = true;
    };
    const onMouseLeave = () => {
      mouse.active = false;
      mouse.x = -9999;
      mouse.y = -9999;
    };

    resize();
    seed();
    raf = requestAnimationFrame(step);
    window.addEventListener('resize', resize);
    document.addEventListener('visibilitychange', onVisibility);
    window.addEventListener('mousemove', onMouseMove, { passive: true });
    window.addEventListener('mouseout', onMouseLeave);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', resize);
      document.removeEventListener('visibilitychange', onVisibility);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseout', onMouseLeave);
    };
  }, [count]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className={`pointer-events-none absolute inset-0 h-full w-full ${className}`}
    />
  );
}
