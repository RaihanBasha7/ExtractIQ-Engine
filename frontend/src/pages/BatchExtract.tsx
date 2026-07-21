import { useRef, useState, useCallback } from 'react';
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
  FileUp,
  File,
  FileSpreadsheet,
  FileCode2,
  Trash2,
  BarChart3,
  Download,
  SplitSquareHorizontal,
  Eye,
  EyeOff,
} from 'lucide-react';
import { GlassCard } from '../components/GlassCard';
import { JsonBlock } from '../components/JsonBlock';
import { api } from '../lib/api';
import type { BatchUploadSummary } from '../lib/api';

const FILE_ACCEPT = '.pdf,.txt,.docx,.csv,.json';

const FILE_ICONS: Record<string, typeof File> = {
  pdf: FileText,
  txt: FileText,
  docx: FileText,
  csv: FileSpreadsheet,
  json: FileCode2,
};

const PIPELINE_STAGES = [
  { id: 'upload', label: 'Upload Document' },
  { id: 'read', label: 'Read Pages' },
  { id: 'detect', label: 'Detect Tickets' },
  { id: 'segments', label: 'Review Segments' },
  { id: 'extract', label: 'AI Extraction' },
  { id: 'wait-provider', label: 'Wait for Provider' },
  { id: 'retry', label: 'Retry' },
  { id: 'validate', label: 'Validation & Repair' },
  { id: 'complete', label: 'Final Results' },
];

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatCSVCell(v: unknown): string {
  if (v === null || v === undefined) return '';
  const s = String(v);
  return s.includes(',') || s.includes('"') ? `"${s.replace(/"/g, '""')}"` : s;
}

export function BatchExtract() {
  const [mode, setMode] = useState<'empty' | 'file' | 'segments' | 'running' | 'result'>('empty');
  const [file, setFile] = useState<File | null>(null);
  const [input, setInput] = useState('');
  const [running, setRunning] = useState(false);
  const [stageIdx, setStageIdx] = useState(0);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [summary, setSummary] = useState<BatchUploadSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showFailed, setShowFailed] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [expandedSegments, setExpandedSegments] = useState<Set<number>>(new Set());
  const [removedSegments, setRemovedSegments] = useState<Set<number>>(new Set());
  const [downloadMenu, setDownloadMenu] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const dropRef = useRef<HTMLDivElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const getFileIcon = (type?: string | null) => {
    if (!type) return File;
    return FILE_ICONS[type.toLowerCase()] ?? File;
  };

  const onFileSelected = useCallback((f: File) => {
    setFile(f);
    setMode('file');
    setSummary(null);
    setError(null);
    setShowFailed(false);
    setShowResults(false);
    setRemovedSegments(new Set());
    setExpandedSegments(new Set());
  }, []);

  const onUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    onFileSelected(f);
    if (fileRef.current) fileRef.current.value = '';
  }, [onFileSelected]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) onFileSelected(f);
  }, [onFileSelected]);

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const onDragLeave = useCallback(() => setDragOver(false), []);

  const clearFile = useCallback(() => {
    setFile(null);
    setInput('');
    setMode('empty');
    setSummary(null);
    setError(null);
    setShowFailed(false);
    setShowResults(false);
    setRemovedSegments(new Set());
    setExpandedSegments(new Set());
  }, []);

  const toggleSegment = useCallback((idx: number) => {
    setExpandedSegments((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  }, []);

  const removeSegment = useCallback((idx: number) => {
    setRemovedSegments((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  }, []);

  const startUpload = useCallback(async () => {
    if (!file || running) return;
    setError(null);
    setSummary(null);
    setRunning(true);
    setStageIdx(0);
    setUploadProgress(0);
    setShowResults(false);
    setMode('running');

    try {
      const result = await api.extractBatchUpload(file, undefined, (_stage, pct) => {
        setUploadProgress(pct);
      });
      setSummary(result);
      setStageIdx(2);

      if (result.segments && result.segments.length > 0) {
        setMode('segments');
        setStageIdx(3);
      } else {
        await runExtraction(result.session_id, result.segments?.map(() => '') ?? []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
      setMode('file');
    } finally {
      setRunning(false);
    }
  }, [file, running]);

  const startText = useCallback(async () => {
    if (!input.trim() || running) return;
    setError(null);
    setSummary(null);
    setRunning(true);
    setStageIdx(0);
    setUploadProgress(0);
    setShowResults(false);
    setMode('running');

    try {
      const result = await api.extractBatchUpload(undefined, input);
      setSummary(result);
      setStageIdx(2);

      if (result.segments && result.segments.length > 0) {
        setMode('segments');
        setStageIdx(3);
      } else {
        await runExtraction(result.session_id, result.segments?.map(() => '') ?? []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Processing failed');
      setMode('empty');
    } finally {
      setRunning(false);
    }
  }, [input, running]);

  const runExtraction = useCallback(async (sessionId: string | null, tickets: string[]) => {
    if (!sessionId) return;
    setRunning(true);
    setMode('running');
    setStageIdx(4);

    const timer = setInterval(() => {
      setStageIdx((prev) => Math.min(prev + 1, PIPELINE_STAGES.length - 1));
    }, 2000);

    try {
      const result = await api.extractBatchProcess(sessionId, tickets);
      clearInterval(timer);
      setStageIdx(PIPELINE_STAGES.length - 1);
      setSummary((prev) => prev ? { ...prev, ...result, results: result.results } : result);
      setMode('result');
      setTimeout(() => setShowResults(true), 300);
    } catch (err) {
      clearInterval(timer);
      setError(err instanceof Error ? err.message : 'Extraction failed');
      setMode('segments');
    } finally {
      setRunning(false);
    }
  }, []);

  const processSegments = useCallback(() => {
    if (!summary?.session_id || !summary?.segments) return;
    const tickets = summary.segments
      .filter((_, i) => !removedSegments.has(i))
      .map((s) => s.preview);
    if (tickets.length === 0) return;
    runExtraction(summary.session_id, tickets);
  }, [summary, removedSegments, runExtraction]);

  const downloadJSON = useCallback(() => {
    if (!summary?.results?.length) return;
    const payload = summary.results.map((r, i) => ({
      ticket_index: i + 1,
      ticket: r.ticket,
      status: r.status,
      final_status: r.final_status,
      confidence_score: r.confidence_score,
      result: r.final_json,
    }));
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'extraction-results.json';
    a.click();
    URL.revokeObjectURL(url);
    setDownloadMenu(false);
  }, [summary]);

  const downloadCSV = useCallback(() => {
    if (!summary?.results?.length) return;
    const headers = ['index', 'ticket', 'final_status', 'confidence_score', 'category', 'urgency', 'customer_name', 'order_ids', 'amounts'];
    const rows = summary.results.map((r, i) => {
      const fj = r.final_json || {};
      return [
        i + 1,
        r.ticket,
        r.final_status,
        r.confidence_score?.toFixed(1),
        formatCSVCell((fj as any).category),
        formatCSVCell((fj as any).urgency),
        formatCSVCell((fj as any).customer?.name ?? (fj as any).customer),
        formatCSVCell(Array.isArray((fj as any).entities?.order_ids) ? (fj as any).entities.order_ids.join(';') : ''),
        formatCSVCell(Array.isArray((fj as any).entities?.amounts_mentioned) ? (fj as any).entities.amounts_mentioned.join(';') : ''),
      ];
    });
    const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'extraction-results.csv';
    a.click();
    URL.revokeObjectURL(url);
    setDownloadMenu(false);
  }, [summary]);

  const downloadFailures = useCallback(() => {
    if (!summary?.results?.length) return;
    const failed = summary.results.filter((r) => (r.final_status === 'NEEDS_REVIEW' || r.status === 'failure') && r.final_status !== 'INFRASTRUCTURE_ERROR');
    if (!failed.length) return;
    const payload = failed.map((r) => ({
      ticket_index: summary.results.indexOf(r) + 1,
      ticket: r.ticket,
      final_status: r.final_status,
      validation_status: r.validation_status,
      needs_review_reason: r.needs_review_reason,
      repair_attempts: r.repair_attempts,
    }));
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'extraction-failures.json';
    a.click();
    URL.revokeObjectURL(url);
    setDownloadMenu(false);
  }, [summary]);

  const validSegments = summary?.segments?.filter((_, i) => !removedSegments.has(i)) ?? [];
  const FileIcon = file ? getFileIcon(file.name.split('.').pop()) : File;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Batch Extract</h1>
          <p className="mt-1.5 text-sm text-white/50">
            Upload documents for automatic ticket detection and AI extraction.
          </p>
        </div>
      </div>

      {mode === 'empty' && !running && (
        <div className="grid lg:grid-cols-2 gap-4">
          <GlassCard hover={false} className="p-5">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <FileUp size={15} className="text-brand-cyan" /> Upload Document
            </h3>
            <div
              ref={dropRef}
              onDrop={onDrop}
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
              className={`relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-10 transition-all cursor-pointer ${
                dragOver
                  ? 'border-brand-blue bg-brand-blue/5'
                  : 'border-white/[0.08] hover:border-white/20 bg-white/[0.02]'
              }`}
              onClick={() => fileRef.current?.click()}
            >
              <div className="w-16 h-16 rounded-2xl bg-white/[0.04] border border-white/[0.06] flex items-center justify-center mb-4">
                <Upload size={28} className="text-white/40" />
              </div>
              <p className="text-sm font-medium text-white/70 mb-1">
                {dragOver ? 'Drop file here' : 'Drop a file or click to browse'}
              </p>
              <p className="text-xs text-white/40">
                PDF, TXT, DOCX, CSV, JSON &mdash; up to 100 MB
              </p>
            </div>
            <input ref={fileRef} type="file" accept={FILE_ACCEPT} onChange={onUpload} className="hidden" />

            <div className="mt-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="h-px flex-1 bg-white/[0.06]" />
                <span className="text-xs text-white/30">or paste text</span>
                <div className="h-px flex-1 bg-white/[0.06]" />
              </div>
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Paste multiple tickets &mdash; one per line..."
                aria-label="Batch text input"
                className="w-full min-h-[140px] resize-none rounded-xl bg-[#0a0e1a] border border-white/[0.06] p-4 text-sm text-white/85 placeholder:text-white/25 outline-none focus:border-brand-blue/40 font-mono"
              />
              <button
                onClick={startText}
                disabled={!input.trim() || running}
                className="btn-primary disabled:opacity-40 mt-3 w-full"
              >
                <Play size={15} />
                Process Text
              </button>
            </div>
          </GlassCard>

          <GlassCard hover={false} className="p-5 flex flex-col items-center justify-center text-center py-16">
            <div className="w-14 h-14 rounded-2xl bg-white/[0.04] border border-white/[0.06] flex items-center justify-center mb-4">
              <SplitSquareHorizontal size={22} className="text-white/30" />
            </div>
            <p className="text-sm text-white/45 max-w-xs">
              Upload a document and the system will automatically detect ticket boundaries using intelligent segmentation, then run AI extraction on each ticket in parallel.
            </p>
          </GlassCard>
        </div>
      )}

      {mode === 'file' && !running && (
        <GlassCard hover={false} className="p-5">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <FileUp size={15} className="text-brand-cyan" /> File Selected
          </h3>
          <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-4 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-brand-blue/10 border border-brand-blue/20 flex items-center justify-center shrink-0">
              <FileIcon size={24} className="text-brand-blue" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{file?.name}</p>
              <p className="text-xs text-white/40 mt-0.5">
                {file ? formatSize(file.size) : ''}
                {file?.name ? ` \u00b7 ${file.name.split('.').pop()?.toUpperCase()}` : ''}
              </p>
            </div>
            <button onClick={clearFile} className="btn-ghost p-2 shrink-0">
              <Trash2 size={15} className="text-red-400" />
            </button>
          </div>
          <div className="flex gap-2 mt-4">
            <button onClick={clearFile} className="btn-ghost flex-1">Cancel</button>
            <button onClick={startUpload} className="btn-primary flex-1" disabled={running}>
              <Upload size={15} />
              Upload &amp; Detect Tickets
            </button>
          </div>
        </GlassCard>
      )}

      {(mode === 'running' && !summary?.segments?.length) && (
        <GlassCard hover={false} className="p-5">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Loader2 size={15} className="text-brand-blue animate-spin" /> Pipeline
          </h3>

          {file && (
            <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-3 flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-brand-blue/10 border border-brand-blue/20 flex items-center justify-center shrink-0">
                <FileIcon size={20} className="text-brand-blue" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{file.name}</p>
                <p className="text-xs text-white/40">{formatSize(file.size)}</p>
              </div>
              {stageIdx === 0 && <span className="text-xs text-brand-blue">{uploadProgress}%</span>}
            </div>
          )}

          <div className="space-y-3">
            {PIPELINE_STAGES.slice(0, 4).map((s, i) => (
              <div key={s.id} className="flex items-center gap-3">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 transition-all ${
                  i < stageIdx ? 'bg-brand-green text-white' :
                  i === stageIdx ? 'bg-brand-blue text-white animate-pulse' :
                  'bg-white/[0.06] text-white/30'
                }`}>
                  {i < stageIdx ? <CheckCircle2 size={14} /> :
                   i === stageIdx ? <Loader2 size={14} className="animate-spin" /> :
                   <div className="w-2 h-2 rounded-full bg-white/20" />}
                </div>
                <div className="flex-1">
                  <p className={`text-sm font-medium ${
                    i < stageIdx ? 'text-brand-green' :
                    i === stageIdx ? 'text-brand-blue' :
                    'text-white/40'
                  }`}>{s.label}</p>
                </div>
                {i === stageIdx && stageIdx === 0 && (
                  <span className="text-xs text-brand-blue font-mono">{uploadProgress}%</span>
                )}
              </div>
            ))}

            {stageIdx >= 2 && (
              <div className="rounded-xl bg-white/[0.03] border border-white/[0.06] p-3 mt-2">
                <p className="text-xs text-white/50">
                  Document ingested and analyzed. Intelligent ticket detection running...
                </p>
              </div>
            )}
          </div>
        </GlassCard>
      )}

      {mode === 'segments' && summary?.segments && (
        <div className="space-y-4">
          <GlassCard hover={false} className="p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <SplitSquareHorizontal size={15} className="text-brand-cyan" />
                Detected Tickets
                <span className="chip bg-brand-cyan/15 text-brand-cyan border border-brand-cyan/20 text-xs ml-2">
                  {validSegments.length} {validSegments.length === 1 ? 'ticket' : 'tickets'}
                </span>
              </h3>
              <div className="flex gap-2">
                <button onClick={clearFile} className="btn-ghost text-xs">Cancel</button>
                <button
                  onClick={processSegments}
                  disabled={validSegments.length === 0 || running}
                  className="btn-primary disabled:opacity-40"
                >
                  {running ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
                  Extract {validSegments.length} {validSegments.length === 1 ? 'Ticket' : 'Tickets'}
                </button>
              </div>
            </div>

            {summary.file_name && (
              <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-3 flex items-center gap-3 mb-4">
                <FileIcon size={20} className="text-white/40" />
                <span className="text-sm text-white/70">{summary.file_name}</span>
                {summary.file_size ? <span className="text-xs text-white/40">{formatSize(summary.file_size)}</span> : null}
                {summary.pages ? <span className="text-xs text-white/40">{summary.pages} pages</span> : null}
                <span className="chip bg-brand-cyan/10 text-brand-cyan text-[10px] border border-brand-cyan/20">
                  {summary.segmentation_method === 'structured' ? 'Structured Dataset' :
                   summary.segmentation_method === 'rule' ? 'Rule-based' :
                   summary.segmentation_method === 'ai' ? 'AI-assisted' :
                   summary.segmentation_method}
                </span>
              </div>
            )}

            {summary.warnings && summary.warnings.length > 0 && (
              <div className="rounded-xl bg-yellow-500/5 border border-yellow-500/20 p-3 mb-4">
                {summary.warnings.map((w, i) => (
                  <p key={i} className="text-xs text-yellow-300/70 flex items-center gap-1">
                    <AlertTriangle size={11} /> {w}
                  </p>
                ))}
              </div>
            )}

            <div className="grid grid-cols-4 gap-2 mb-4">
              <Stat label="Total Detected" value={summary.segments.length} color="text-white" />
              <Stat label="Valid" value={validSegments.length} color="text-brand-green" />
              <Stat label="Removed" value={removedSegments.size} color="text-red-400" />
              <Stat label="Method" value={summary.segmentation_method === 'structured' ? 'Structured' : summary.segmentation_method === 'rule' ? 'Rules' : summary.segmentation_method === 'ai' ? 'AI' : 'Auto'} color="text-brand-cyan" />
            </div>

            <div className="space-y-2 max-h-[420px] overflow-y-auto no-scrollbar">
              <AnimatePresence>
                {summary.segments.map((seg, i) => {
                  if (removedSegments.has(i)) return null;
                  const expanded = expandedSegments.has(i);
                  return (
                    <motion.div
                      key={i}
                      layout
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      className={`rounded-xl border p-3 ${
                        seg.valid
                          ? 'bg-white/[0.02] border-white/[0.06]'
                          : 'bg-yellow-500/5 border-yellow-500/20'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2">
                          <span className="chip bg-brand-cyan/10 text-brand-cyan border border-brand-cyan/20 text-[10px]">
                            Ticket {i + 1}
                          </span>
                          <span className="text-[10px] text-white/40">
                            {seg.word_count} words
                          </span>
                          <span className="text-[10px] text-white/30">
                            {seg.boundary_type}
                          </span>
                          {!seg.valid && (
                            <span className="text-[10px] text-yellow-400">{seg.validation_message}</span>
                          )}
                        </div>
                        <div className="flex gap-1">
                          <button onClick={() => toggleSegment(i)} className="btn-ghost p-1">
                            {expanded ? <EyeOff size={13} /> : <Eye size={13} />}
                          </button>
                          <button onClick={() => removeSegment(i)} className="btn-ghost p-1">
                            <Trash2 size={13} className="text-red-400" />
                          </button>
                        </div>
                      </div>
                      <p className={`text-xs font-mono ${expanded ? 'text-white/80 whitespace-pre-wrap' : 'text-white/50 truncate'}`}>
                        {expanded ? seg.preview : seg.preview}
                      </p>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
          </GlassCard>
        </div>
      )}

      {(mode === 'running' && mode !== 'segments' && summary?.segments?.length) && (
        <GlassCard hover={false} className="p-5">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Loader2 size={15} className="text-brand-blue animate-spin" /> Processing {validSegments.length} Tickets
          </h3>

          <div className="space-y-3">
            {PIPELINE_STAGES.map((s, i) => (
              <div key={s.id} className="flex items-center gap-3">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 transition-all ${
                  i < stageIdx ? 'bg-brand-green text-white' :
                  i === stageIdx ? 'bg-brand-blue text-white animate-pulse' :
                  'bg-white/[0.06] text-white/30'
                }`}>
                  {i < stageIdx ? <CheckCircle2 size={14} /> :
                   i === stageIdx ? <Loader2 size={14} className="animate-spin" /> :
                   <div className="w-2 h-2 rounded-full bg-white/20" />}
                </div>
                <div className="flex-1">
                  <p className={`text-sm font-medium ${
                    i < stageIdx ? 'text-brand-green' :
                    i === stageIdx ? 'text-brand-blue' :
                    'text-white/40'
                  }`}>{s.label}</p>
                  {i === stageIdx && i === 4 && (
                    <p className="text-xs text-white/40 mt-0.5">
                      Processing {validSegments.length} tickets with async concurrency control
                    </p>
                  )}
                  {i === stageIdx && i === 5 && (
                    <p className="text-xs text-white/40 mt-0.5">
                      Waiting for provider rate-limit window
                    </p>
                  )}
                  {i === stageIdx && i === 6 && (
                    <p className="text-xs text-white/40 mt-0.5">
                      Auto-retry on infrastructure errors (up to 3 attempts)
                    </p>
                  )}
                </div>
              </div>
            ))}

            <div className="rounded-xl bg-white/[0.03] border border-white/[0.06] p-3 mt-2">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-white/50">Parallel Processing</span>
                <span className="text-xs text-brand-blue">Active</span>
              </div>
              <div className="flex gap-1">
                {Array.from({ length: Math.min(validSegments.length, 20) }, (_, i) => (
                  <div
                    key={i}
                    className="flex-1 h-1.5 rounded-full bg-brand-blue/30 animate-pulse"
                    style={{ animationDelay: `${i * 100}ms` }}
                  />
                ))}
              </div>
              <p className="text-xs text-white/30 mt-2">
                Each ticket is processed independently. Failures do not affect other tickets.
              </p>
            </div>
          </div>
        </GlassCard>
      )}

      {error && (
        <GlassCard hover={false} className="p-5 border-red-500/20">
          <div className="flex items-center gap-2">
            <AlertTriangle size={15} className="text-red-400 shrink-0" />
            <span className="text-sm text-red-300">{error}</span>
          </div>
          <button onClick={() => { setError(null); setMode('empty'); }} className="btn-ghost mt-3 text-xs">
            Try Again
          </button>
        </GlassCard>
      )}

      {mode === 'result' && summary && !running && (
        <div className="space-y-4">
          <GlassCard hover={false} className="p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <CheckCircle2 size={15} className="text-brand-green" /> Results
              </h3>
              <div className="flex gap-2 relative">
                <button onClick={() => { clearFile(); setMode('empty'); }} className="btn-ghost">
                  <Upload size={14} /> New Batch
                </button>
                <div className="relative">
                  <button onClick={() => setDownloadMenu(!downloadMenu)} className="btn-primary">
                    <Download size={14} /> Download
                  </button>
                  {downloadMenu && (
                    <div className="absolute right-0 top-full mt-1 w-48 rounded-xl bg-[#0a0e1a] border border-white/[0.08] shadow-xl z-10 overflow-hidden">
                      <button onClick={downloadJSON} className="w-full text-left px-3 py-2 text-xs text-white/70 hover:bg-white/[0.04] flex items-center gap-2">
                        <FileCode2 size={13} /> All JSON
                      </button>
                      <button onClick={downloadCSV} className="w-full text-left px-3 py-2 text-xs text-white/70 hover:bg-white/[0.04] flex items-center gap-2">
                        <FileSpreadsheet size={13} /> CSV Summary
                      </button>
                      <button onClick={downloadFailures} className="w-full text-left px-3 py-2 text-xs text-white/70 hover:bg-white/[0.04] flex items-center gap-2">
                        <AlertTriangle size={13} /> Failure Report
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {summary.file_name && (
              <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-3 flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-brand-green/10 border border-brand-green/20 flex items-center justify-center shrink-0">
                  <CheckCircle2 size={20} className="text-brand-green" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{summary.file_name}</p>
                  <p className="text-xs text-white/40">
                    {summary.file_type}
                    {summary.file_size ? ` \u00b7 ${formatSize(summary.file_size)}` : ''}
                    {summary.pages ? ` \u00b7 ${summary.pages} page${summary.pages > 1 ? 's' : ''}` : ''}
                    {summary.tickets_detected ? ` \u00b7 ${summary.tickets_detected} tickets` : ''}
                  </p>
                </div>
              </div>
            )}

            {summary.warnings && summary.warnings.length > 0 && (
              <div className="rounded-xl bg-yellow-500/5 border border-yellow-500/20 p-3 mb-4">
                {summary.warnings.map((w, i) => (
                  <p key={i} className="text-xs text-yellow-300/70 flex items-center gap-1">
                    <AlertTriangle size={11} /> {w}
                  </p>
                ))}
              </div>
            )}

            <div className="grid grid-cols-7 gap-2 mb-4">
              <Stat label="Detected" value={summary.tickets_detected || summary.processed} color="text-white" />
              <Stat label="Processed" value={summary.processed} color="text-white" />
              <Stat label="Success" value={summary.successful} color="text-brand-green" />
              <Stat label="Repaired" value={summary.repaired} color="text-yellow-400" />
              <Stat label="Needs Review" value={summary.needs_review} color="text-orange-400" />
              <Stat label="Failed" value={summary.failed} color="text-red-400" />
              <Stat label="Provider Retry" value={summary.infrastructure_retry} color="text-purple-400" />
            </div>

            <div className="h-2 rounded-full bg-white/[0.06] overflow-hidden">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-brand-green via-yellow-400 to-red-500"
                initial={{ width: 0 }}
                animate={{
                  width: summary.processed > 0
                    ? `${((summary.successful + summary.repaired) / summary.processed) * 100}%`
                    : '0%',
                }}
                transition={{ duration: 1, ease: 'easeOut' }}
              />
            </div>
            <div className="flex justify-between mt-1">
              <span className="text-[10px] text-white/30">Success Rate</span>
              <span className="text-[10px] text-white/40">
                {summary.processed > 0
                  ? `${Math.round(((summary.successful + summary.repaired) / summary.processed) * 100)}%`
                  : '0%'}
              </span>
            </div>
          </GlassCard>

          {showResults && summary.results.length > 0 && (
            <GlassCard hover={false} className="p-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Layers size={15} className="text-brand-cyan" /> Ticket Results ({summary.results.length})
                </h3>
              </div>

              <div className="space-y-2 max-h-[400px] overflow-y-auto no-scrollbar">
                <AnimatePresence>
                  {summary.results.map((r, idx) => (
                    <motion.div
                      key={r.id || idx}
                      layout
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.03 }}
                      className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-3"
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <ResultBadge finalStatus={r.final_status} />
                        <span className="text-xs text-white/50 truncate flex-1">
                          {r.ticket || `Ticket ${idx + 1}`}
                        </span>
                        <span className="text-[10px] font-mono text-white/30">
                          {r.confidence_score?.toFixed(0)}%
                        </span>
                      </div>

                      {r.final_json && Object.keys(r.final_json).length > 0 && (
                        <div className="rounded-lg bg-[#0a0e1a] border border-white/[0.05] p-2 mt-1">
                          <pre className="text-[10px] text-white/60 font-mono whitespace-pre-wrap line-clamp-3">
                            {JSON.stringify(r.final_json, null, 1)}
                          </pre>
                        </div>
                      )}

                      <div className="flex gap-1 mt-1.5">
                        <span className="text-[9px] text-white/20">
                          {r.repair_attempts?.length
                            ? `${r.repair_attempts.filter((a) => a.status === 'failed').length} repair(s)`
                            : 'No repairs'}
                        </span>
                        {r.needs_review_reason && (
                          <span className="text-[9px] text-orange-400/60 ml-2 truncate">
                            {r.needs_review_reason}
                          </span>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </GlassCard>
          )}

          {showResults && summary.results.filter((r) => r.final_status === 'NEEDS_REVIEW' || r.final_status === 'INFRASTRUCTURE_ERROR' || r.status === 'failure').length > 0 && (
            <GlassCard hover={false} className="p-5 border-red-500/20">
              <button
                onClick={() => setShowFailed(!showFailed)}
                className="flex items-center gap-2 w-full text-left"
              >
                <AlertTriangle size={15} className="text-yellow-400 shrink-0" />
                <span className="text-sm font-medium text-white">
                  {summary.needs_review + summary.failed + summary.infrastructure_retry} ticket{(summary.needs_review + summary.failed + summary.infrastructure_retry) > 1 ? 's' : ''} need review
                </span>
              </button>
              {showFailed && (
                <div className="mt-3 space-y-2">
                  {summary.results.filter((r) => r.final_status === 'NEEDS_REVIEW' || r.final_status === 'INFRASTRUCTURE_ERROR' || r.status === 'failure').map((r, i) => {
                    const isInfra = r.final_status === 'INFRASTRUCTURE_ERROR';
                    return (
                      <div key={r.id || i} className={`rounded-lg bg-[#0a0e1a] border p-3 ${
                        isInfra ? 'border-purple-500/20' : 'border-white/[0.05]'
                      }`}>
                        <p className="text-xs text-white/60 font-mono truncate">{r.ticket || 'Unknown'}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`text-[10px] ${isInfra ? 'text-purple-400' : 'text-red-400'}`}>
                            {isInfra ? 'Provider rate limited' : r.validation_status === 'failed' ? 'Validation failed' : 'Needs review'}
                          </span>
                          {r.needs_review_reason && (
                            <span className="text-[10px] text-white/40">{r.needs_review_reason}</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </GlassCard>
          )}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="rounded-lg bg-white/[0.02] border border-white/[0.05] p-2.5">
      <p className={`text-lg font-bold ${color}`}>{value}</p>
      <p className="text-[9px] text-white/40">{label}</p>
    </div>
  );
}

function ResultBadge({ finalStatus }: { finalStatus?: string }) {
  const map: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
    SUCCESS: { icon: <CheckCircle2 size={11} />, color: 'bg-brand-green/15 text-brand-green', label: 'Success' },
    REPAIRED: { icon: <CheckCircle2 size={11} />, color: 'bg-yellow-500/15 text-yellow-400', label: 'Repaired' },
    NEEDS_REVIEW: { icon: <AlertTriangle size={11} />, color: 'bg-orange-500/15 text-orange-400', label: 'Review' },
    INFRASTRUCTURE_ERROR: { icon: <AlertTriangle size={11} />, color: 'bg-purple-500/15 text-purple-400', label: 'Provider Rate Limited' },
  };
  const s = map[finalStatus ?? 'NEEDS_REVIEW'] ?? map.NEEDS_REVIEW;
  return (
    <span className={`chip ${s.color} border border-white/[0.06]`}>
      {s.icon}
      {s.label}
    </span>
  );
}
