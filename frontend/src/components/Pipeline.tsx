import { Save, ChevronDown, CheckCircle2, Recycle, Inbox, Sparkles } from 'lucide-react';
import { PIPELINE_STAGES, STAGE_ICONS, NODES, nodeActiveAt } from './pipelineConstants';
import type { PipelineStage } from '../types';

interface PipelineTimelineProps {
  stages: PipelineStage[];
  activeIndex: number;
  inRepair?: boolean;
}

export function PipelineTimeline({ stages, activeIndex, inRepair = false }: PipelineTimelineProps) {
  return (
    <div className="space-y-2.5">
      {stages.map((stage, i) => {
        const Icon = STAGE_ICONS[stage.id] ?? Inbox;
        const isActive = i === activeIndex;
        const isDone = i < activeIndex;
        const isRepair = stage.id === 'repair';
        return (
          <div
            key={stage.id}
            className={`relative flex items-center gap-3 rounded-xl px-3 py-2.5 border transition-all duration-300 ${
              isActive
                ? 'bg-brand-blue/10 border-brand-blue/40 shadow-glow'
                : isDone
                  ? 'bg-brand-green/[0.04] border-brand-green/20'
                  : 'bg-white/[0.02] border-white/[0.05]'
            }`}
          >
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 transition-all ${
                isActive
                  ? 'bg-gradient-to-br from-brand-blue to-brand-cyan text-white'
                  : isDone
                    ? 'bg-brand-green/15 text-brand-green'
                    : 'bg-white/[0.04] text-white/30'
              }`}
            >
              {isDone ? <CheckCircle2 size={15} /> : <Icon size={15} />}
            </div>
            <div className="flex-1 min-w-0">
              <p
                className={`text-sm font-medium ${
                  isActive ? 'text-white' : isDone ? 'text-white/70' : 'text-white/40'
                }`}
              >
                {stage.label}
                {isRepair && inRepair && (
                  <span className="ml-2 text-[10px] text-brand-green font-semibold uppercase tracking-wider animate-pulse-slow">
                    looping
                  </span>
                )}
              </p>
              <p className="text-[11px] text-white/35 truncate">{stage.description}</p>
            </div>
            {isActive && (
              <span className="animate-spin-slow">
                <Sparkles size={13} className="text-brand-cyan" fill="currentColor" />
              </span>
            )}
            {i < stages.length - 1 && (
              <div className="absolute left-[27px] top-full w-px h-2.5 bg-white/10" />
            )}
          </div>
        );
      })}
    </div>
  );
}

interface NodeFlowProps {
  activeIndex: number;
  inRepair?: boolean;
  completed?: boolean;
}

export function NodeFlow({ activeIndex, inRepair = false, completed = false }: NodeFlowProps) {
  const active = nodeActiveAt(activeIndex);
  const isRunning = activeIndex >= 0 && activeIndex < PIPELINE_STAGES.length;

  return (
    <div className="relative">
      <div className="relative flex flex-col gap-3">
        {NODES.map((node, i) => {
          const isActive = completed ? node.id === 'final' : active.includes(node.id);
          const isRepairNode = node.id === 'repair';
          return (
            <div key={node.id} className="relative">
              <div
                className={`relative flex items-center gap-3 rounded-2xl px-4 py-3 border bg-white/[0.02] transition-all duration-400 ${
                  isActive
                    ? completed
                      ? 'border-brand-green/50 shadow-[0_0_30px_-6px_rgba(34,197,94,0.6)] scale-[1.02]'
                      : 'border-brand-blue/50 shadow-[0_0_30px_-6px_rgba(59,130,246,0.6)] scale-[1.02]'
                    : 'border-white/[0.06]'
                }`}
              >
                <div
                  className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
                    isActive
                      ? completed
                        ? 'bg-gradient-to-br from-brand-green to-brand-cyan text-white'
                        : 'bg-gradient-to-br from-brand-blue to-brand-cyan text-white'
                      : 'bg-white/[0.04] text-white/40'
                  }`}
                >
                  <node.icon size={18} />
                </div>
                <div className="flex-1">
                  <p className={`text-sm font-semibold ${isActive ? 'text-white' : 'text-white/55'}`}>
                    {node.label}
                  </p>
                </div>
                {isActive && !completed && (
                  <span
                    className="w-2 h-2 rounded-full bg-brand-cyan animate-ping-slow"
                  />
                )}
                {completed && node.id === 'final' && (
                  <span>
                    <CheckCircle2 size={18} className="text-brand-green" />
                  </span>
                )}
              </div>

              {i < NODES.length - 1 && (
                <div className="flex justify-center py-1">
                  <div className="relative w-px h-5 bg-white/10 overflow-hidden">
                    {isRunning && active.includes(node.id) && !completed && (
                      <span
                        className="absolute left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-brand-cyan"
                        style={{ boxShadow: '0 0 8px #06B6D4', animation: 'slideDown 0.8s ease-in infinite' }}
                      />
                    )}
                    {completed && (
                      <span className="absolute left-0 top-0 w-px h-full bg-brand-green" />
                    )}
                  </div>
                </div>
              )}

              {isRepairNode && inRepair && !completed && (
                <div className="absolute -right-3 top-1/2 -translate-y-1/2 hidden md:flex items-center">
                  <div className="flex flex-col items-center">
                    <span className="animate-spin-slow">
                      <Recycle size={14} className="text-brand-green" />
                    </span>
                    <span className="text-[9px] text-brand-green mt-1">loop</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

interface OutputSectionProps {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
  icon?: React.ReactNode;
}

export function OutputSection({ title, defaultOpen = false, children, icon }: OutputSectionProps) {
  return (
    <div className="glass rounded-xl border border-white/[0.06] overflow-hidden">
      <details open={defaultOpen} className="group">
        <summary className="flex items-center justify-between px-4 py-3 cursor-pointer list-none hover:bg-white/[0.02] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue/40 rounded-xl">
          <span className="flex items-center gap-2 text-sm font-medium text-white/80">
            {icon}
            {title}
          </span>
          <ChevronDown size={16} className="text-white/40 group-open:rotate-180 transition-transform duration-200" />
        </summary>
        <div className="px-4 pb-4 pt-1">{children}</div>
      </details>
    </div>
  );
}

export function DownloadButton({ data, filename }: { data: unknown; filename: string }) {
  const download = () => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };
  return (
    <button onClick={download} className="btn-ghost">
      <Save size={15} /> Download JSON
    </button>
  );
}
