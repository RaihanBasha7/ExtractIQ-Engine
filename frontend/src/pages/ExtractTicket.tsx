import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play,
  Eraser,
  FileText,
  Sparkles,
  BrainCircuit,
  Cpu,
  Clock,
  Target,
  Calendar,
  Recycle,
  RotateCcw,
  DollarSign,
  Truck,
  Wifi,
  CreditCard,
  Lock,
} from 'lucide-react';
import { SAMPLE_TICKETS } from '../lib/sampleTicket';
import type { SampleTicket } from '../lib/sampleTicket';
import { useExtraction } from '../lib/useExtraction';
import { GlassCard } from '../components/GlassCard';
import { JsonBlock } from '../components/JsonBlock';
import { ErrorCard } from '../components/ErrorCard';
import {
  PipelineTimeline,
  NodeFlow,
  OutputSection,
  DownloadButton,
} from '../components/Pipeline';
import { PIPELINE_STAGES } from '../components/pipelineConstants';

const CATEGORY_ICONS: Record<string, typeof DollarSign> = {
  Billing: DollarSign,
  Shipping: Truck,
  'Technical Issue': Wifi,
  Refund: CreditCard,
  'Account Problem': Lock,
};

export function ExtractTicket() {
  const [ticket, setTicket] = useState('');
  const { state, activeStage, inRepair, result, error, run, reset } = useExtraction();
  const running = state === 'running';

  const charCount = ticket.length;

  const loadSample = useCallback((sample: SampleTicket) => {
    setTicket(sample.ticket);
    reset();
  }, [reset]);

  const clear = useCallback(() => {
    setTicket('');
    reset();
  }, [reset]);

  const handleRun = useCallback(() => {
    if (ticket.trim()) run(ticket);
  }, [ticket, run]);

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Single Extract</h1>
          <p className="mt-1.5 text-sm text-white/50">
            Paste a raw support ticket and watch the full extraction pipeline execute in real time.
          </p>
        </div>
        <span className="chip bg-brand-blue/10 text-brand-blue border border-brand-blue/20">
          <Sparkles size={12} /> Inside the AI
        </span>
      </div>

      {/* Sample ticket selector */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
        {SAMPLE_TICKETS.map((sample) => {
          const Icon = CATEGORY_ICONS[sample.category] ?? FileText;
          return (
            <button
              key={sample.id}
              onClick={() => loadSample(sample)}
              disabled={running}
              className="flex items-center gap-2.5 rounded-xl px-3.5 py-2.5 border border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.04] hover:border-white/[0.12] transition-all text-left disabled:opacity-40"
            >
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-blue/20 to-brand-cyan/10 flex items-center justify-center shrink-0">
                <Icon size={14} className="text-brand-cyan" />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-medium text-white/80 truncate">{sample.label}</p>
                <p className="text-[10px] text-white/40">{sample.category}</p>
              </div>
            </button>
          );
        })}
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        {/* LEFT: input */}
        <GlassCard hover={false} className="p-5 flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <FileText size={15} className="text-brand-cyan" /> Support Ticket
            </h3>
            <span className="text-[11px] text-white/40">{charCount} chars</span>
          </div>
          <textarea
            value={ticket}
            onChange={(e) => setTicket(e.target.value)}
            placeholder="Paste your support ticket here&hellip;"
            aria-label="Support ticket input"
            className="flex-1 min-h-[280px] resize-none rounded-xl bg-[#0a0e1a] border border-white/[0.06] p-4 text-sm text-white/85 placeholder:text-white/25 outline-none focus:border-brand-blue/40 transition-colors font-mono leading-relaxed"
          />
          <div className="flex items-center justify-between mt-4 flex-wrap gap-2">
            <div className="flex gap-2">
              <button onClick={clear} className="btn-ghost" disabled={running}>
                <Eraser size={14} /> Clear
              </button>
            </div>
<button
              onClick={handleRun}
              disabled={!ticket.trim() || running}
              className="btn-primary disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {running ? (
                <span className="animate-spin">🔄</span>
              ) : (
                <Play size={15} />
              )} {running ? 'Analyzing Ticket...' : 'Run Extraction'}
            </button>
          </div>
        </GlassCard>

        {/* RIGHT: pipeline visualization */}
        <GlassCard hover={false} className="p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <BrainCircuit size={15} className="text-brand-blue" /> Pipeline
            </h3>
            <span className="text-[11px] text-white/40">
              {activeStage >= 0 && activeStage < 7
                ? `Stage ${activeStage + 1} / 7`
                : state === 'done'
                  ? 'Complete'
                  : 'Idle'}
            </span>
          </div>

          <AnimatePresence mode="wait">
            {running || result ? (
              <motion.div
                key="flow"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <NodeFlow
                  activeIndex={activeStage}
                  inRepair={inRepair}
                  completed={state === 'done'}
                />
              </motion.div>
            ) : (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="h-full flex flex-col items-center justify-center text-center py-12"
              >
                <div className="w-14 h-14 rounded-2xl bg-white/[0.04] border border-white/[0.06] flex items-center justify-center mb-4">
                  <Cpu size={22} className="text-white/30" />
                </div>
                <p className="text-sm text-white/45 max-w-xs">
                  The pipeline will light up stage-by-stage once you run an extraction.
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </GlassCard>
      </div>

      {/* Timeline strip */}
      <AnimatePresence>
        {running && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <GlassCard hover={false} className="p-5">
              <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                <Clock size={15} className="text-brand-cyan" /> Execution Timeline
              </h3>
              <PipelineTimeline stages={PIPELINE_STAGES} activeIndex={activeStage} inRepair={inRepair} />
            </GlassCard>
          </motion.div>
        )}
      </AnimatePresence>

      {error && <ErrorCard onRetry={handleRun} />}

      {/* Output panel - always render when result exists */}
      <AnimatePresence>
        {result && (
          <motion.div
            key={result.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <div className="flex items-center justify-between flex-wrap gap-3">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Sparkles size={18} className="text-brand-green" /> Extraction Output
              </h2>
              <div className="flex gap-2">
                <button onClick={clear} className="btn-ghost">
                  <RotateCcw size={14} /> Reset
                </button>
                <DownloadButton data={result.final_json} filename={`extraction-${result.id}.json`} />
              </div>
            </div>

            <div className="grid lg:grid-cols-3 gap-4">
              <div className="lg:col-span-2 space-y-3">
                <OutputSection title="Original Ticket" icon={<FileText size={14} className="text-white/50" />}>
                  <pre className="text-xs text-white/70 whitespace-pre-wrap font-mono leading-relaxed bg-[#0a0e1a] rounded-lg p-3 border border-white/[0.05]">
                    {result.ticket}
                  </pre>
                </OutputSection>
                <OutputSection title="Cleaned Text" icon={<Eraser size={14} className="text-white/50" />}>
                  <pre className="text-xs text-white/70 whitespace-pre-wrap font-mono leading-relaxed bg-[#0a0e1a] rounded-lg p-3 border border-white/[0.05]">
                    {result.cleaned_text}
                  </pre>
                </OutputSection>
                <OutputSection title="Structured Extraction" defaultOpen icon={<BrainCircuit size={14} className="text-white/50" />}>
                  <JsonBlock data={result.structured_extraction} maxHeight="300px" />
                </OutputSection>
                {result.repair_attempts.length > 0 && (
                  <OutputSection title={`Repair Attempts (${result.repair_attempts.length})`} icon={<Recycle size={14} className="text-white/50" />}>
                    <div className="space-y-2">
                      {result.repair_attempts.map((a) => (
                        <div key={a.attempt} className="rounded-lg bg-[#0a0e1a] border border-white/[0.05] p-3">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`chip ${
                              a.status === 'success'
                                ? 'bg-brand-green/10 text-brand-green border-brand-green/20'
                                : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
                            }`}>
                              Attempt #{a.attempt}
                            </span>
                            <span className={`text-[10px] ${a.status === 'success' ? 'text-brand-green' : 'text-yellow-400'}`}>
                              {a.status === 'success' ? 'resolved' : 'failed'}
                            </span>
                          </div>
                          {a.error && (
                            <p className="text-xs text-white/60 mt-1">{a.error}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </OutputSection>
                )}
                <OutputSection title="Final Guaranteed JSON" defaultOpen icon={<Sparkles size={14} className="text-brand-green" />}>
                  <JsonBlock data={result.final_json} maxHeight="400px" />
                </OutputSection>
              </div>

              {/* Metadata panel */}
              <GlassCard hover={false} className="p-5 h-fit lg:sticky lg:top-24">
                <h3 className="text-sm font-semibold text-white mb-4">Metadata</h3>
                <div className="space-y-3">
                  <MetaRow icon={<Cpu size={13} />} label="Provider" value={result.metadata.provider} />
                  <MetaRow icon={<BrainCircuit size={13} />} label="Model" value={result.metadata.model} />
                  <MetaRow icon={<Clock size={13} />} label="Latency" value={`${result.metadata.latency_ms} ms`} />
                  <MetaRow icon={<Target size={13} />} label="Confidence" value={`${(result.metadata.confidence * 100).toFixed(1)}%`} />
                  <MetaRow icon={<Recycle size={13} />} label="Repair attempts" value={String(result.metadata.repair_attempts)} />
                  <MetaRow icon={<Calendar size={13} />} label="Timestamp" value={new Date(result.metadata.timestamp).toLocaleString()} />
                </div>
                <div className="mt-5 p-3 rounded-xl bg-brand-green/[0.06] border border-brand-green/20 flex items-center gap-2">
                  <Sparkles size={14} className="text-brand-green" />
                  <span className="text-xs text-brand-green font-medium">Schema validated &amp; guaranteed</span>
                </div>
              </GlassCard>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function MetaRow({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-white/[0.04] last:border-0">
      <span className="flex items-center gap-2 text-xs text-white/45">
        <span className="text-white/40">{icon}</span>
        {label}
      </span>
      <span className="text-xs font-medium text-white/85 text-right max-w-[60%] truncate">{value}</span>
    </div>
  );
}
