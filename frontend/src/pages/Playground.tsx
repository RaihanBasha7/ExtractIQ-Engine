import { useState, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  Play,
  RotateCcw,
  Copy,
  Check,
  Save,
  Inbox,
  Brush,
  BrainCircuit,
  ShieldCheck,
  Recycle,
  CheckCircle2,
  XCircle,
  Wifi,
  RefreshCw,
  CreditCard,
  Lock,
  Truck,
  ChevronDown,
  Braces,
  Cpu,
  Tag,
  Clock,
  Gauge,
  Loader2,
  type LucideIcon,
} from 'lucide-react';
import { EXAMPLE_TICKETS } from '../lib/examples';
import { useExtraction } from '../lib/useExtraction';
import { GlassCard } from '../components/GlassCard';
import { JsonBlock } from '../components/JsonBlock';
import {
  ConfidenceRing,
  EntityHighlightedText,
  FieldMappingTable,
  SchemaValidationChecklist,
  ExtractionSummaryCards,
  ExplainabilityPanel,
  LiveExtractionInsights,
  findFieldMappings,
} from '../components/PlaygroundShowcase';

const EXAMPLE_ICONS: Record<string, LucideIcon> = {
  wifi: Wifi,
  refund: RefreshCw,
  card: CreditCard,
  lock: Lock,
  truck: Truck,
};

const PIPELINE_STAGES_LIST = [
  { id: 'upload', label: 'Upload', icon: Inbox, desc: 'Receiving ticket payload' },
  { id: 'preprocess', label: 'Preprocessing', icon: Brush, desc: 'Cleaning & PII stripping' },
  { id: 'extract', label: 'LLM Extraction', icon: BrainCircuit, desc: 'AI analyzing intent & entities' },
  { id: 'validate', label: 'Validation', icon: ShieldCheck, desc: 'Schema check v1.2.0' },
  { id: 'repair', label: 'Repair Loop', icon: Recycle, desc: 'Patching schema violations' },
  { id: 'final', label: 'Guaranteed JSON', icon: Braces, desc: 'Validated structured output' },
];

export function Playground() {
  const [selectedExample, setSelectedExample] = useState(EXAMPLE_TICKETS[0].id);
  const { state, activeStage, inRepair, held, result, error, run, reset } = useExtraction();
  const [copied, setCopied] = useState(false);
  const running = state === 'running';

  const example = EXAMPLE_TICKETS.find((e) => e.id === selectedExample)!;

  const fieldMappings = useMemo(
    () => (result ? findFieldMappings(result.final_json, result.ticket) : []),
    [result],
  );

  const fieldCount = useMemo(() => {
    if (!result) return 0;
    let count = 0;
    function walk(obj: unknown) {
      if (obj && typeof obj === 'object' && !Array.isArray(obj)) {
        const entries = Object.entries(obj as Record<string, unknown>);
        for (const [, v] of entries) {
          if (v !== null && typeof v === 'object') walk(v);
          else count++;
        }
      }
    }
    walk(result.final_json);
    return count;
  }, [result]);

  const handleRun = useCallback(() => {
    run(example.ticket);
  }, [run, example.ticket]);

  const handleReset = useCallback(() => {
    reset();
  }, [reset]);

  const copyJson = async () => {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(JSON.stringify(result.final_json, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch { /* ignore */ }
  };

  const download = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result.final_json, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `playground-${result.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const stageStatus = (index: number): 'done' | 'active' | 'pending' | 'held' => {
    if (result) return 'done';
    if (state === 'error') return 'pending';
    if (activeStage < 0) return 'pending';
    if (index < activeStage) return 'done';
    if (index === activeStage) {
      if (index === 5 && held) return 'held';
      return 'active';
    }
    return 'pending';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>
            AI Playground
          </h1>
          <p className="mt-1.5 text-sm max-w-2xl" style={{ color: 'var(--text-secondary)' }}>
            Visualize the intelligence behind ExtractIQ Engine. Pick an example ticket and watch the
            full pipeline produce guaranteed JSON.
          </p>
        </div>
        <span className="chip bg-brand-cyan/10 text-brand-cyan border border-brand-cyan/20">
          <Sparkles size={12} /> Showcase mode
        </span>
      </div>

      {/* Example selector */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] mb-3" style={{ color: 'var(--text-tertiary)' }}>
          Example tickets
        </p>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2.5">
          {EXAMPLE_TICKETS.map((ex) => {
            const Icon = EXAMPLE_ICONS[ex.icon] ?? Inbox;
            const active = ex.id === selectedExample;
            return (
              <button
                key={ex.id}
                onClick={() => !running && setSelectedExample(ex.id)}
                disabled={running}
                className={`relative flex flex-col items-start gap-2 rounded-xl p-3 border text-left transition-all ${
                  active
                    ? 'bg-brand-blue/10 border-brand-blue/40 shadow-glow'
                    : 'bg-white/[0.02] border-white/[0.06] hover:bg-white/[0.04] hover:border-white/[0.12]'
                } disabled:opacity-50`}
              >
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    active ? 'bg-gradient-to-br from-brand-blue to-brand-cyan text-white' : 'bg-white/[0.04] text-white/55'
                  }`}
                >
                  <Icon size={15} />
                </div>
                <span className={`text-xs font-medium ${active ? 'text-white' : 'text-white/65'}`}>{ex.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="grid lg:grid-cols-5 gap-4">
        {/* LEFT: Pipeline visualization (3 cols) */}
        <div className="lg:col-span-3 space-y-4">
          {/* Input card */}
          <GlassCard hover={false} className="p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                <Inbox size={15} className="text-brand-cyan" /> Support Ticket
              </h3>
              <span className="text-[11px]" style={{ color: 'var(--text-tertiary)' }}>{example.ticket.length} chars</span>
            </div>
            <div className="text-xs whitespace-pre-wrap font-mono leading-relaxed bg-[#0a0e1a] rounded-lg p-3 border border-white/[0.05] min-h-[140px] max-h-[200px] overflow-auto no-scrollbar">
              <AnimatePresence mode="wait">
                {result && fieldMappings.length > 0 ? (
                  <motion.div
                    key="highlighted"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.4 }}
                  >
                    <EntityHighlightedText text={result.ticket} mappings={fieldMappings} />
                  </motion.div>
                ) : (
                  <motion.span key="plain" initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ color: 'var(--text-secondary)' }}>
                    {example.ticket}
                  </motion.span>
                )}
              </AnimatePresence>
            </div>
            <div className="flex items-center justify-between mt-4 flex-wrap gap-2">
              <button onClick={handleReset} className="btn-ghost" disabled={running}>
                <RotateCcw size={14} /> Reset
              </button>
              <button
                onClick={handleRun}
                disabled={running}
                className="btn-primary disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {running ? (
                  <Loader2 size={15} className="animate-spin" />
                ) : (
                  <Play size={15} />
                )} {running ? 'Generating...' : 'Run Demo'}
              </button>
            </div>
          </GlassCard>

          {/* Pipeline Stages - true synchronized visualization */}
          <GlassCard hover={false} className="p-5">
            <h3 className="text-sm font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
              <BrainCircuit size={15} className="text-brand-blue" /> Pipeline Stages
            </h3>
            <div className="relative flex flex-col">
              {PIPELINE_STAGES_LIST.map((stage, i) => {
                const status = stageStatus(i);
                const isActive = status === 'active';
                const isDone = status === 'done';
                const isHeld = status === 'held';
                const isPending = status === 'pending';
                return (
                  <div key={stage.id} className="relative">
                    <motion.div
                      layout
                      className={`relative flex items-center gap-3 rounded-2xl px-4 py-3 border transition-all duration-500 ${
                        isActive
                          ? 'border-brand-blue/50 shadow-[0_0_30px_-6px_rgba(59,130,246,0.5)] bg-brand-blue/[0.08] scale-[1.01]'
                          : isDone
                            ? 'border-brand-green/30 bg-brand-green/[0.04]'
                            : isHeld
                              ? 'border-yellow-500/40 shadow-[0_0_25px_-6px_rgba(234,179,8,0.3)] bg-yellow-500/[0.06]'
                              : 'border-white/[0.06] bg-white/[0.02]'
                      }`}
                    >
                      {/* Stage icon */}
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 transition-all duration-500 ${
                        isActive
                          ? 'bg-gradient-to-br from-brand-blue to-brand-cyan text-white shadow-glow'
                          : isDone
                            ? 'bg-brand-green/15 text-brand-green'
                            : isHeld
                              ? 'bg-yellow-500/15 text-yellow-400'
                              : 'bg-white/[0.04] text-white/40'
                      }`}>
                        {isDone ? <CheckCircle2 size={18} /> : <stage.icon size={18} />}
                      </div>

                      {/* Stage label */}
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm font-semibold ${
                          isActive ? 'text-white' : isDone ? 'text-white/80' : isHeld ? 'text-yellow-300' : 'text-white/55'
                        }`}>
                          {stage.label}
                          {isHeld && (
                            <span className="ml-2 text-[10px] text-yellow-400 font-semibold uppercase tracking-wider">
                              waiting
                            </span>
                          )}
                          {isDone && stage.id === 'repair' && inRepair && (
                            <span className="ml-2 text-[10px] text-brand-green font-semibold uppercase tracking-wider animate-pulse-slow">
                              looped
                            </span>
                          )}
                        </p>
                        <p className="text-[11px] text-white/35 truncate">{stage.desc}</p>
                      </div>

                      {/* Status indicator */}
                      <div className="shrink-0 flex items-center">
                        {isActive && (
                          <motion.span
                            className="w-3 h-3 rounded-full bg-brand-cyan block"
                            animate={{ scale: [1, 1.8, 1], opacity: [1, 0.3, 1] }}
                            transition={{ duration: 1.2, repeat: Infinity, ease: 'easeInOut' }}
                          />
                        )}
                        {isHeld && (
                          <motion.div
                            className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-yellow-500/10 border border-yellow-500/20"
                            animate={{ opacity: [0.7, 1, 0.7] }}
                            transition={{ duration: 1.5, repeat: Infinity }}
                          >
                            <Loader2 size={11} className="text-yellow-400 animate-spin" />
                            <span className="text-[10px] text-yellow-300 font-medium">Waiting for model...</span>
                          </motion.div>
                        )}
                        {isDone && i === 5 && (
                          <CheckCircle2 size={18} className="text-brand-green" />
                        )}
                      </div>
                    </motion.div>

                    {/* Animated connector between stages */}
                    {i < PIPELINE_STAGES_LIST.length - 1 && (
                      <div className="flex justify-center py-0.5">
                        <div className="relative w-0.5 h-4 overflow-hidden">
                          <div className={`absolute inset-0 transition-colors duration-500 ${
                            isDone ? 'bg-brand-green/50' : 'bg-white/10'
                          }`} />
                          {isActive && (
                            <motion.div
                              className="absolute inset-x-0 top-0 h-1/2 bg-gradient-to-b from-brand-cyan to-transparent"
                              animate={{ top: ['0%', '100%'] }}
                              transition={{ duration: 0.8, repeat: Infinity, ease: 'linear' }}
                            />
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </GlassCard>

          {/* Live Extraction Insights */}
          {running && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
            >
              <GlassCard hover={false} className="p-5">
                <h3 className="text-sm font-semibold mb-3 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                  <Gauge size={15} className="text-brand-cyan" /> Live Extraction Insights
                </h3>
                <LiveExtractionInsights activeStage={activeStage} held={held} />
              </GlassCard>
            </motion.div>
          )}
        </div>

        {/* RIGHT: Output area (2 cols) */}
        <div className="lg:col-span-2 space-y-4">
          {error && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <GlassCard hover={false} className="p-5 border-red-500/20">
                <p className="text-sm text-red-400">Extraction failed. Try again or pick another example.</p>
                <button onClick={handleRun} className="btn-primary mt-3">
                  <Play size={14} /> Retry
                </button>
              </GlassCard>
            </motion.div>
          )}

          {/* Status indicator while running (pre-final stages) */}
          {running && !held && !result && (
            <GlassCard hover={false} className="p-5">
              <div className="flex items-center gap-3">
                <motion.span
                  className="w-3 h-3 rounded-full bg-brand-cyan"
                  animate={{ scale: [1, 1.5, 1], opacity: [1, 0.5, 1] }}
                  transition={{ duration: 1, repeat: Infinity }}
                />
                <div>
                  <p className="text-sm font-medium text-white">Processing ticket&hellip;</p>
                  <p className="text-xs text-white/40">Stage {Math.min(activeStage + 1, 6)} / 6</p>
                </div>
              </div>
            </GlassCard>
          )}

          {/* Held state - waiting for backend */}
          {held && !result && (
            <motion.div
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3 }}
            >
              <GlassCard hover={false} className="p-5 border-yellow-500/20">
                <div className="flex items-center gap-3">
                  <motion.div
                    className="w-10 h-10 rounded-xl bg-yellow-500/10 border border-yellow-500/20 flex items-center justify-center"
                    animate={{ scale: [1, 1.05, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    <Loader2 size={18} className="text-yellow-400 animate-spin" />
                  </motion.div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-yellow-300">Awaiting model response</p>
                    <p className="text-xs text-yellow-400/60 mt-0.5">
                      LLM is processing the ticket. Results will appear automatically.
                    </p>
                  </div>
                </div>
                {/* Animated progress bar */}
                <div className="mt-3 h-1 rounded-full bg-white/[0.06] overflow-hidden">
                  <motion.div
                    className="h-full rounded-full bg-gradient-to-r from-yellow-500 to-yellow-400"
                    animate={{ x: ['-100%', '100%'] }}
                    transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
                    style={{ width: '60%' }}
                  />
                </div>
              </GlassCard>
            </motion.div>
          )}

          {/* Result sections - only show when result exists */}
          <AnimatePresence>
            {result && (
              <motion.div
                key="result"
                className="space-y-4"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
              >
                {/* Success banner */}
                <GlassCard hover={false} className="p-5 border-brand-green/20">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-brand-green/15 border border-brand-green/20 flex items-center justify-center">
                      <CheckCircle2 size={20} className="text-brand-green" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-brand-green">Extraction Complete</p>
                      <p className="text-xs text-white/40 mt-0.5">Guaranteed JSON ready for inspection</p>
                    </div>
                    <div className="ml-auto flex gap-2">
                      <button onClick={copyJson} className="btn-ghost text-xs px-3 py-1.5">
                        {copied ? <Check size={12} /> : <Copy size={12} />}
                        {copied ? 'Copied' : 'Copy'}
                      </button>
                      <button onClick={download} className="btn-ghost text-xs px-3 py-1.5">
                        <Save size={12} /> Download
                      </button>
                    </div>
                  </div>
                </GlassCard>

                {/* Structured JSON */}
                <GlassCard hover={false} className="p-5">
                  <h3 className="text-sm font-semibold mb-3 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                    <Braces size={15} className="text-brand-green" /> Structured JSON
                    {fieldMappings.length > 0 && (
                      <span className="chip bg-brand-blue/10 text-brand-blue border border-brand-blue/20 text-[10px] ml-auto">
                        <Tag size={10} /> {fieldMappings.length} entities
                      </span>
                    )}
                  </h3>
                  <JsonBlock data={result.final_json} maxHeight="360px" />
                </GlassCard>

                {/* Schema Validation */}
                <GlassCard hover={false} className="p-5">
                  <h3 className="text-sm font-semibold mb-3 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                    <ShieldCheck size={15} className="text-brand-green" /> Schema Validation
                  </h3>
                  <SchemaValidationChecklist showAll />
                </GlassCard>

                {/* AI Reasoning */}
                <GlassCard hover={false} className="p-5">
                  <ExplainabilityPanel
                    json={result.final_json}
                    ticket={result.ticket}
                    confidence={result.metadata.confidence}
                  />
                </GlassCard>

                {/* Extraction Summary */}
                <GlassCard hover={false} className="p-5">
                  <h3 className="text-sm font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                    <Cpu size={15} className="text-brand-cyan" /> Extraction Summary
                  </h3>
                  <div className="flex items-start gap-5 mb-4">
                    <div className="flex flex-col items-center gap-1 shrink-0">
                      <ConfidenceRing value={result.metadata.confidence} />
                      <span className="text-[10px] text-white/40">Confidence</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <ExtractionSummaryCards
                        latencyMs={result.metadata.latency_ms}
                        confidence={result.metadata.confidence}
                        repairAttempts={result.metadata.repair_attempts}
                        fieldCount={fieldCount}
                        provider={result.metadata.provider}
                        model={result.metadata.model}
                        validationStatus="Valid"
                      />
                    </div>
                  </div>

                  {/* Metadata grid */}
                  <div className="grid grid-cols-2 gap-3 text-sm mt-3">
                    <Meta label="Request ID" value={result.id} mono />
                    <Meta label="Provider" value={result.metadata.provider} />
                    <Meta label="Model" value={result.metadata.model} mono />
                    <Meta label="Repair Attempts" value={String(result.metadata.repair_attempts)} />
                    <Meta label="Timestamp" value={new Date(result.metadata.timestamp).toLocaleString()} />
                    <Meta label="Schema Status" value="Validated" />
                  </div>

                  {/* Confidence bar */}
                  <div className="mt-4">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs text-white/50">Confidence Score</span>
                      <span className="text-xs font-semibold text-white">
                        {(result.metadata.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="h-2 rounded-full bg-white/[0.06] overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${result.metadata.confidence * 100}%` }}
                        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
                        className="h-full rounded-full bg-gradient-to-r from-brand-blue to-brand-cyan"
                      />
                    </div>
                  </div>
                </GlassCard>

                {/* Repair Timeline */}
                {result.repair_attempts.length > 0 && (
                  <GlassCard hover={false} className="p-5">
                    <h3 className="text-sm font-semibold mb-3 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                      <Recycle size={15} className="text-brand-cyan" /> Repair Timeline
                    </h3>
                    <div className="space-y-2">
                      {result.repair_attempts.map((a) => (
                        <div key={a.attempt} className="flex items-center gap-2 text-sm">
                          <div className={`w-5 h-5 rounded-full flex items-center justify-center ${
                            a.status === 'success' ? 'bg-brand-green/15 text-brand-green' : 'bg-yellow-500/15 text-yellow-400'
                          }`}>
                            {a.status === 'success' ? <CheckCircle2 size={11} /> : <XCircle size={11} />}
                          </div>
                          <span className="text-white/50">Attempt #{a.attempt}</span>
                          <span className={a.status === 'success' ? 'text-brand-green' : 'text-yellow-400'}>
                            {a.status === 'success' ? 'Resolved' : a.error || 'Failed'}
                          </span>
                        </div>
                      ))}
                      <p className="text-xs text-white/40 mt-2">
                        Schema violations patched automatically via repair loop.
                      </p>
                    </div>
                  </GlassCard>
                )}

                {result.repair_attempts.length === 0 && (
                  <GlassCard hover={false} className="p-5 border-brand-green/20">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 size={15} className="text-brand-green" />
                      <div>
                        <p className="text-sm font-medium text-brand-green">Passed on first attempt</p>
                        <p className="text-xs text-white/40 mt-0.5">No repair needed &mdash; schema validated successfully.</p>
                      </div>
                    </div>
                  </GlassCard>
                )}

                {/* Preprocessed text */}
                <GlassCard hover={false} className="p-5">
                  <h3 className="text-sm font-semibold mb-3 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                    <Brush size={15} className="text-brand-cyan" /> Preprocessed Ticket
                  </h3>
                  <pre className="text-xs text-white/70 whitespace-pre-wrap font-mono leading-relaxed bg-[#0a0e1a] rounded-lg p-3 border border-white/[0.05] max-h-[120px] overflow-auto no-scrollbar">
                    {result.cleaned_text || result.ticket}
                  </pre>
                </GlassCard>

                {/* Field Mapping table */}
                {fieldMappings.length > 0 && (
                  <GlassCard hover={false} className="p-5">
                    <h3 className="text-sm font-semibold mb-3 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                      <Tag size={15} className="text-brand-cyan" /> Field Mapping
                    </h3>
                    <p className="text-[11px] text-white/40 mb-3">
                      Hover highlighted entities in the original ticket above to see their JSON field path.
                    </p>
                    <FieldMappingTable mappings={fieldMappings} />
                  </GlassCard>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Empty state */}
          {!result && !running && !error && (
            <GlassCard hover={false} className="p-5">
              <div className="h-[200px] flex flex-col items-center justify-center text-center">
                <div className="w-12 h-12 rounded-2xl bg-white/[0.04] border border-white/[0.06] flex items-center justify-center mb-3">
                  <Sparkles size={20} className="text-white/30" />
                </div>
                <p className="text-sm text-white/45 max-w-xs">
                  Run a demo to see the ticket transform into guaranteed, schema-valid JSON.
                </p>
              </div>
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  );
}

function Meta({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="rounded-lg bg-white/[0.02] border border-white/[0.05] px-3 py-2">
      <p className="text-[10px] uppercase tracking-wider text-white/35">{label}</p>
      <p className={`text-sm text-white/85 mt-0.5 truncate ${mono ? 'font-mono' : ''}`}>{value}</p>
    </div>
  );
}
