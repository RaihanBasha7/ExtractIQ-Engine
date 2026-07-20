import { useRef, useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Layers,
  Upload,
  Play,
  Save,
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  FileText,
  AlertTriangle,
  ChevronRight,
} from 'lucide-react';
import { GlassCard } from '../components/GlassCard';
import { JsonBlock } from '../components/JsonBlock';
import { api } from '../lib/api';
import type { ExtractionResult, ExtractionStatus } from '../types';

const BATCH_STAGES = [
  { id: 'queued', label: 'Queued' },
  { id: 'preprocess', label: 'Preprocessing' },
  { id: 'extract', label: 'AI Extraction' },
  { id: 'validate', label: 'Validation' },
  { id: 'repair', label: 'Repair' },
  { id: 'complete', label: 'Completed' },
];

interface BatchItem {
  id: string;
  text: string;
  status: ExtractionStatus | 'queued';
  progress: number;
  stageIndex: number;
  result?: Record<string, unknown>;
}

const SAMPLE_DATASETS: { label: string; data: string }[] = [
  {
    label: 'Small Batch (3)',
    data: [
      'My internet has been down for 3 days, please help! Account AC-12345.',
      'I was charged twice for my subscription this month. Need refund on card ending 4401.',
      'The mobile app crashes every time I open settings. iPhone 14 Pro, iOS 17.5.',
    ].join('\n'),
  },
  {
    label: 'Medium Batch (6)',
    data: [
      'Cannot login after password reset. Account AC-77812.',
      'Order #ORD-45521 never arrived. Need replacement shipped overnight.',
      'Billing error: charged $49.99 instead of $29.99 for Pro plan.',
      'Feature request: please add dark mode to the web dashboard.',
      'My team member didnt receive the invite email. Sent 2 days ago.',
      'API key was revoked without warning. Need it restored immediately.',
    ].join('\n'),
  },
  {
    label: 'Mixed Categories (5)',
    data: [
      'Refund request for duplicate payment of $299. Order ORD-88421.',
      'Technician no-show for the 3rd time. Appointment #APPT-5512.',
      'Cannot export my workspace data to CSV. Get error EXP-403.',
      'Trial period ended early. Was supposed to have 14 days, ended on day 7.',
      'Security concern: unauthorized login attempt detected from IP 203.0.113.42.',
    ].join('\n'),
  },
  {
    label: 'Customer Support (4)',
    data: [
      'How do I transfer my workspace to a different email address?',
      'My uploaded files are not showing up in the shared drive.',
      'The search function returns zero results for terms I know exist.',
      'I need an invoice for all payments made in 2024 for my accountant.',
    ].join('\n'),
  },
  {
    label: 'Refund Batch (4)',
    data: [
      'Requesting refund for order #ORD-33910. Product arrived damaged.',
      'Double charged for enterprise plan. Need $599 refunded.',
      'Subscription auto-renewed without notification. Cancel and refund.',
      'I returned the item 3 weeks ago but still no refund processed.',
    ].join('\n'),
  },
];

function isEmptyJson(obj: Record<string, unknown>): boolean {
  return Object.keys(obj).length === 0;
}

function isValidResult(r?: Record<string, unknown>): boolean {
  return !!r && !isEmptyJson(r);
}

const STAGE_ADVANCE_MS = 80;

export function BatchExtract() {
  const [input, setInput] = useState('');
  const [items, setItems] = useState<BatchItem[]>([]);
  const [running, setRunning] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showFailed, setShowFailed] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  const start = useCallback(async () => {
    const tickets = input
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);
    if (!tickets.length || running) return;

    const parsed: BatchItem[] = tickets.map((text, i) => ({
      id: `b${i}_${Date.now()}`,
      text,
      status: 'queued',
      progress: 0,
      stageIndex: 0,
    }));
    setItems(parsed);
    setRunning(true);
    setCurrentIndex(0);

    for (let i = 0; i < parsed.length; i++) {
      if (!mountedRef.current) break;
      setCurrentIndex(i);

      setItems((prev) =>
        prev.map((it, idx) =>
          idx === i ? { ...it, status: 'running', progress: 5, stageIndex: 1 } : it,
        ),
      );

      const apiPromise = api.extract(tickets[i]);

      const stageTimers: ReturnType<typeof setTimeout>[] = [];
      for (let s = 2; s < BATCH_STAGES.length - 1; s++) {
        const timer = setTimeout(() => {
          if (mountedRef.current) {
            setItems((prev) =>
              prev.map((it, idx) =>
                idx === i
                  ? { ...it, stageIndex: s, progress: (s / (BATCH_STAGES.length - 1)) * 100 }
                  : it,
              ),
            );
          }
        }, (s - 1) * STAGE_ADVANCE_MS);
        stageTimers.push(timer);
      }

      try {
        const r = await apiPromise;
        stageTimers.forEach(clearTimeout);
        if (!mountedRef.current) break;
        setItems((prev) =>
          prev.map((it, idx) =>
            idx === i
              ? { ...it, stageIndex: BATCH_STAGES.length - 1, status: 'completed', progress: 100, result: r.final_json }
              : it,
          ),
        );
      } catch {
        stageTimers.forEach(clearTimeout);
        if (!mountedRef.current) break;
        try {
          const r = await api.extract(tickets[i]);
          setItems((prev) =>
            prev.map((it, idx) =>
              idx === i
                ? { ...it, stageIndex: BATCH_STAGES.length - 1, status: 'completed', progress: 100, result: r.final_json }
                : it,
            ),
          );
        } catch {
          setItems((prev) =>
            prev.map((it, idx) =>
              idx === i
                ? { ...it, stageIndex: BATCH_STAGES.length - 1, status: 'failure', progress: 100 }
                : it,
            ),
          );
        }
      }
    }
    setRunning(false);
  }, [input, running]);

  const onUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => setInput(String(reader.result ?? ''));
    reader.readAsText(file);
  };

  const downloadAll = () => {
    const validItems = items.filter((it) => isValidResult(it.result));
    const payload = validItems.map((it) => ({ id: it.id, status: it.status, ticket: it.text, result: it.result }));
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'batch-extraction.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const completed = items.filter((i) => i.status === 'completed').length;
  const failed = items.filter((i) => i.status === 'failure').length;
  const totalProgress = items.length > 0 ? (completed / items.length) * 100 : 0;

  const validResults = items.filter((it) => isValidResult(it.result)).map((it) => it.result!);
  const failedTickets = items.filter((it) => it.status === 'failure' || (it.status === 'completed' && !isValidResult(it.result)));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">Batch Extract</h1>
        <p className="mt-1.5 text-sm text-white/50">
          Process many tickets at once. One ticket per line, or upload a file.
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <GlassCard hover={false} className="p-5">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Layers size={15} className="text-brand-cyan" /> Input
          </h3>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Paste multiple tickets &mdash; one per line&hellip;"
            aria-label="Batch input"
            className="w-full min-h-[220px] resize-none rounded-xl bg-[#0a0e1a] border border-white/[0.06] p-4 text-sm text-white/85 placeholder:text-white/25 outline-none focus:border-brand-blue/40 font-mono"
          />
          <div className="flex flex-wrap gap-2 mt-4">
            <div className="flex flex-wrap gap-1.5">
              {SAMPLE_DATASETS.map((ds) => (
                <button
                  key={ds.label}
                  onClick={() => setInput(ds.data)}
                  className="btn-ghost text-xs px-2.5 py-1.5"
                  disabled={running}
                >
                  <FileText size={11} /> {ds.label}
                </button>
              ))}
            </div>
            <div className="flex-1" />
            <button onClick={() => fileRef.current?.click()} className="btn-ghost" disabled={running}>
              <Upload size={14} /> Upload
            </button>
            <input ref={fileRef} type="file" accept=".jsonl,.txt,.json" onChange={onUpload} className="hidden" />
            <button onClick={start} disabled={!input.trim() || running} className="btn-primary disabled:opacity-40">
              {running ? (
                <span className="animate-spin">🔄</span>
              ) : (
                <Play size={15} />
              )}
              {running
                ? `Processing Ticket ${currentIndex + 1} of ${items.length}...`
                : 'Run Batch'}
            </button>
          </div>
        </GlassCard>

        <GlassCard hover={false} className="p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">Progress</h3>
            {items.length > 0 && (
              <button onClick={downloadAll} className="btn-ghost">
                <Save size={14} /> Download
              </button>
            )}
          </div>

          {items.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center py-16">
              <div className="w-14 h-14 rounded-2xl bg-white/[0.04] border border-white/[0.06] flex items-center justify-center mb-4">
                <Layers size={22} className="text-white/30" />
              </div>
              <p className="text-sm text-white/45 max-w-xs">
                Batch results will appear here. Each ticket animates through preprocessing, extraction, and validation.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {running && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-white/70">
                      Ticket {currentIndex + 1} of {items.length}
                    </span>
                    <span className="text-xs text-white/40">{Math.round(totalProgress)}%</span>
                  </div>
                  <div className="h-2 rounded-full bg-white/[0.06] overflow-hidden">
                    <motion.div
                      className="h-full rounded-full bg-gradient-to-r from-brand-blue to-brand-cyan"
                      animate={{ width: `${totalProgress}%` }}
                      transition={{ duration: 0.5, ease: 'easeOut' }}
                    />
                  </div>
                </div>
              )}

              <div className="grid grid-cols-3 gap-2 text-center">
                <Stat label="Total" value={items.length} color="text-white" />
                <Stat label="Completed" value={completed} color="text-brand-green" />
                <Stat label="Failed" value={failed} color="text-red-400" />
              </div>

              <div className="space-y-2 max-h-[360px] overflow-y-auto no-scrollbar">
                <AnimatePresence>
                  {items.map((it) => (
                    <motion.div
                      key={it.id}
                      layout
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-3"
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <StatusBadge status={it.status} stageIndex={it.stageIndex} />
                        <span className="text-xs text-white/50 truncate flex-1">{it.text}</span>
                      </div>

                      <div className="flex gap-0.5 h-1.5 mb-1.5">
                        {BATCH_STAGES.map((stage, idx) => (
                          <div
                            key={stage.id}
                            className={`flex-1 rounded-full transition-all duration-500 ${
                              idx < it.stageIndex
                                ? 'bg-brand-green'
                                : idx === it.stageIndex
                                  ? it.status === 'failure'
                                    ? 'bg-red-500'
                                    : 'bg-brand-blue'
                                  : 'bg-white/[0.06]'
                            }`}
                          />
                        ))}
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1 flex-wrap">
                          {BATCH_STAGES.map((stage, idx) => (
                            <span
                              key={stage.id}
                              className={`text-[9px] font-medium transition-colors duration-300 ${
                                idx === it.stageIndex
                                  ? it.status === 'failure'
                                    ? 'text-red-400'
                                    : 'text-brand-blue'
                                  : idx < it.stageIndex
                                    ? 'text-brand-green/60'
                                    : 'text-white/20'
                              }`}
                            >
                              {idx > 0 && <ChevronRight size={8} className="inline mx-0.5 text-white/15" />}
                              {stage.label}
                            </span>
                          ))}
                        </div>
                        {it.status === 'running' && (
                          <span className="text-[9px] text-brand-blue/60 font-mono">{Math.round(it.progress)}%</span>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </div>
          )}
        </GlassCard>
      </div>

      {validResults.length > 0 && (
        <GlassCard hover={false} className="p-5">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <CheckCircle2 size={15} className="text-brand-green" /> Valid Results ({validResults.length})
          </h3>
          <JsonBlock data={validResults} maxHeight="300px" />
        </GlassCard>
      )}

      {failedTickets.length > 0 && (
        <GlassCard hover={false} className="p-5 border-red-500/20">
          <button
            onClick={() => setShowFailed(!showFailed)}
            className="flex items-center gap-2 w-full text-left"
          >
            <AlertTriangle size={15} className="text-yellow-400 shrink-0" />
            <span className="text-sm font-medium text-white">
              {failedTickets.length} ticket{failedTickets.length > 1 ? 's' : ''} had empty or failed results
            </span>
          </button>
          {showFailed && (
            <div className="mt-3 space-y-2">
              {failedTickets.map((it) => (
                <div key={it.id} className="rounded-lg bg-[#0a0e1a] border border-white/[0.05] p-3">
                  <p className="text-xs text-white/60 font-mono">{it.text}</p>
                  <span className="text-[10px] text-red-400 mt-1 block">No valid extraction data</span>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      )}
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="rounded-lg bg-white/[0.02] border border-white/[0.05] p-2.5">
      <p className={`text-xl font-bold ${color}`}>{value}</p>
      <p className="text-[10px] text-white/40">{label}</p>
    </div>
  );
}

function StatusBadge({ status, stageIndex }: { status: ExtractionStatus | 'queued'; stageIndex: number }) {
  const stage = BATCH_STAGES[stageIndex] ?? BATCH_STAGES[0];
  if (status === 'running') {
    return (
      <span className="chip bg-brand-blue/15 text-brand-blue border border-brand-blue/20">
        <Loader2 size={11} className="animate-spin" />
        {stage.label}
      </span>
    );
  }
  const map: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
    queued: { icon: <Clock size={11} />, color: 'bg-white/[0.06] text-white/60', label: 'Queued' },
    completed: { icon: <CheckCircle2 size={11} />, color: 'bg-brand-green/15 text-brand-green', label: 'Completed' },
    failure: { icon: <XCircle size={11} />, color: 'bg-red-500/15 text-red-400', label: 'Failure' },
  };
  const s = map[status] ?? map.queued;
  return (
    <span className={`chip ${s.color} border border-white/[0.06]`}>
      {s.icon}
      {s.label}
    </span>
  );
}
