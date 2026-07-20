import {
  Upload,
  BrainCircuit,
  ShieldCheck,
  Recycle,
  Braces,
  type LucideIcon,
} from 'lucide-react';

const stages: { label: string; icon: LucideIcon; color: string; glow: string }[] = [
  { label: 'Upload Ticket', icon: Upload, color: 'from-brand-blue to-brand-cyan', glow: 'rgba(59,130,246,0.4)' },
  { label: 'AI Extraction', icon: BrainCircuit, color: 'from-brand-cyan to-brand-blue', glow: 'rgba(6,182,212,0.4)' },
  { label: 'Validation', icon: ShieldCheck, color: 'from-brand-cyan to-brand-green', glow: 'rgba(6,182,212,0.4)' },
  { label: 'Repair Loop', icon: Recycle, color: 'from-brand-green to-brand-cyan', glow: 'rgba(34,197,94,0.4)' },
  { label: 'Guaranteed JSON', icon: Braces, color: 'from-brand-green to-brand-blue', glow: 'rgba(34,197,94,0.4)' },
];

export function WorkflowStrip() {
  return (
    <div className="flex flex-wrap items-center justify-center gap-2 md:gap-3">
      {stages.map((s, i) => (
        <div key={s.label} className="flex items-center gap-2 md:gap-3">
          <div
            className="group relative glass rounded-xl px-4 py-2.5 text-sm font-medium text-white/85 cursor-default transition-all duration-300 hover:border-white/[0.18] hover:bg-white/[0.06] hover:-translate-y-1 hover:scale-[1.02]"
            style={{ '--glow': s.glow } as React.CSSProperties}
          >
            <span
              className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"
              style={{ boxShadow: `0 0 30px -6px ${s.glow}` }}
            />
            <span className={`absolute inset-x-2 -bottom-px h-px bg-gradient-to-r ${s.color} opacity-60 group-hover:opacity-100 transition-opacity`} />
            <span className="relative flex items-center gap-2">
              <span className="text-white/60 group-hover:text-white transition-colors">
                <s.icon size={15} />
              </span>
              <span className="text-white/40 mr-1 text-xs">0{i + 1}</span>
              {s.label}
            </span>
          </div>
          {i < stages.length - 1 && (
            <div className="w-6 md:w-10 h-px bg-gradient-to-r from-white/20 to-white/40" />
          )}
        </div>
      ))}
    </div>
  );
}
