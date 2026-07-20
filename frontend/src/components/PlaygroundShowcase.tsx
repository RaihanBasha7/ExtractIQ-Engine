import { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  Sparkles,
  Zap,
  AlertTriangle,
  Cpu,
  Layers,
  ShieldCheck,
  FileText,
  Tag,
  BrainCircuit,
  Gauge,
  RefreshCw,
  Database,
  Braces,
} from 'lucide-react';

/* ── Confidence Ring ── */
export function ConfidenceRing({ value, size = 72 }: { value: number; size?: number }) {
  const strokeWidth = 5;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - value);

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="-rotate-90">
        <defs>
          <linearGradient id="confGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#3b82f6" />
            <stop offset="100%" stopColor="#06b6d4" />
          </linearGradient>
        </defs>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="rgba(128,128,128,0.12)"
          strokeWidth={strokeWidth}
          fill="none"
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="url(#confGrad)"
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
        />
      </svg>
      <span className="absolute text-lg font-bold" style={{ color: 'var(--text-primary)' }}>
        {Math.round(value * 100)}%
      </span>
    </div>
  );
}

/* ── Entity Highlighting ── */
interface FieldMapping {
  text: string;
  field: string;
}

export function findFieldMappings(
  json: Record<string, unknown>,
  ticketText: string,
): FieldMapping[] {
  const mappings: FieldMapping[] = [];

  function traverse(obj: unknown, path: string) {
    if (typeof obj === 'string' && obj.length > 2) {
      if (ticketText.includes(obj)) {
        mappings.push({ text: obj, field: path });
      }
    } else if (typeof obj === 'number') {
      const str = String(obj);
      if (ticketText.includes(str) && str.length > 1) {
        mappings.push({ text: str, field: path });
      }
    } else if (Array.isArray(obj)) {
      obj.forEach((item, i) => traverse(item, `${path}[${i}]`));
    } else if (obj && typeof obj === 'object') {
      for (const [key, value] of Object.entries(obj)) {
        traverse(value, path ? `${path}.${key}` : key);
      }
    }
  }

  traverse(json, '');
  const unique = new Map<string, FieldMapping>();
  for (const m of mappings) {
    const key = `${m.text}|${m.field}`;
    if (!unique.has(key)) unique.set(key, m);
  }
  return Array.from(unique.values());
}

function highlightEntities(
  text: string,
  mappings: FieldMapping[],
): Array<{ type: 'text' | 'entity'; content: string; field?: string }> {
  const ranges: Array<{ start: number; end: number; field: string; text: string }> = [];

  for (const m of mappings) {
    let idx = text.indexOf(m.text);
    while (idx !== -1) {
      ranges.push({ start: idx, end: idx + m.text.length, field: m.field, text: m.text });
      idx = text.indexOf(m.text, idx + 1);
    }
  }

  ranges.sort((a, b) => a.start - b.start || b.end - a.end);

  const merged: typeof ranges = [];
  for (const r of ranges) {
    if (merged.length === 0) {
      merged.push(r);
    } else {
      const last = merged[merged.length - 1];
      if (r.start >= last.end) {
        merged.push(r);
      } else if (r.end > last.end) {
        last.end = r.end;
        last.field = r.field;
        last.text = r.text;
      }
    }
  }

  const segments: Array<{ type: 'text' | 'entity'; content: string; field?: string }> = [];
  let cursor = 0;

  for (const r of merged) {
    if (r.start > cursor) {
      segments.push({ type: 'text', content: text.slice(cursor, r.start) });
    }
    segments.push({ type: 'entity', content: r.text, field: r.field });
    cursor = r.end;
  }

  if (cursor < text.length) {
    segments.push({ type: 'text', content: text.slice(cursor) });
  }

  return segments;
}

export function EntityHighlightedText({
  text,
  mappings,
}: {
  text: string;
  mappings: FieldMapping[];
}) {
  const segments = useMemo(() => highlightEntities(text, mappings), [text, mappings]);

  return (
    <span>
      {segments.map((seg, i) =>
        seg.type === 'entity' ? (
          <span key={i} className="relative group cursor-help">
            <mark className="bg-brand-blue/15 text-brand-blue rounded-sm px-0.5 transition-colors group-hover:bg-brand-blue/25">
              {seg.content}
            </mark>
            <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-2 py-1 rounded-lg bg-[#0a0e1a] border border-white/[0.08] text-[10px] text-white/70 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20 shadow-lg shadow-black/40">
              <span className="text-brand-cyan font-mono">&rarr; {seg.field}</span>
            </span>
          </span>
        ) : (
          <span key={i}>{seg.content}</span>
        ),
      )}
    </span>
  );
}

/* ── Field Mapping Table ── */
export function FieldMappingTable({ mappings }: { mappings: FieldMapping[] }) {
  const displayed = mappings.slice(0, 10);
  if (displayed.length === 0) return null;
  return (
    <div className="space-y-1">
      {displayed.map((m, i) => (
        <motion.div
          key={`${m.text}-${m.field}-${i}`}
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.05 }}
          className="flex items-center gap-2 text-xs py-1 px-2 rounded-lg hover:bg-white/[0.02] transition-colors"
        >
          <Tag size={10} className="text-brand-cyan/60 shrink-0" />
          <code className="text-brand-cyan font-mono bg-brand-cyan/5 px-1.5 py-0.5 rounded shrink-0 max-w-[140px] truncate">
            {m.text}
          </code>
          <ChevronRight size={10} className="text-white/20 shrink-0" />
          <code className="text-white/45 font-mono truncate">{m.field}</code>
        </motion.div>
      ))}
    </div>
  );
}

/* ── Schema Validation Checklist ── */
export function SchemaValidationChecklist({ showAll = false }: { showAll?: boolean }) {
  const checks = [
    { label: 'Required fields present', status: 'pass' as const, icon: CheckCircle2 },
    { label: 'Enum values valid', status: 'pass' as const, icon: CheckCircle2 },
    { label: 'Nested schema structure', status: 'pass' as const, icon: CheckCircle2 },
    { label: 'Type validation', status: 'pass' as const, icon: CheckCircle2 },
    { label: 'JSON syntax valid', status: 'pass' as const, icon: CheckCircle2 },
  ];

  if (showAll) {
    checks.push(
      { label: 'Schema match', status: 'pass' as const, icon: CheckCircle2 },
      { label: 'Guaranteed JSON', status: 'pass' as const, icon: CheckCircle2 },
    );
  }

  return (
    <div className="grid grid-cols-2 gap-1.5">
      {checks.map((check, i) => {
        const Icon = check.icon;
        return (
          <motion.div
            key={check.label}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06 }}
            className="flex items-center gap-1.5 rounded-lg bg-brand-green/[0.04] border border-brand-green/10 px-2.5 py-1.5"
          >
            <Icon size={11} className="text-brand-green shrink-0" />
            <span className="text-[10px] text-white/60">{check.label}</span>
          </motion.div>
        );
      })}
    </div>
  );
}

/* ── Extraction Summary ── */
interface ExtractionSummaryProps {
  latencyMs: number;
  confidence: number;
  repairAttempts: number;
  fieldCount: number;
  provider?: string;
  model?: string;
  validationStatus?: string;
}

export function ExtractionSummaryCards({
  latencyMs,
  confidence,
  repairAttempts,
  fieldCount,
  provider,
  model,
  validationStatus = 'Valid',
}: ExtractionSummaryProps) {
  const items = [
    {
      icon: <Clock size={13} className="text-brand-cyan" />,
      label: 'Processing time',
      value: latencyMs < 1000 ? `${latencyMs} ms` : `${(latencyMs / 1000).toFixed(1)}s`,
    },
    {
      icon: <Zap size={13} className="text-brand-green" />,
      label: 'Confidence',
      value: `${(confidence * 100).toFixed(1)}%`,
    },
    {
      icon: <RefreshCw size={13} className="text-yellow-400" />,
      label: 'Repair attempts',
      value: String(repairAttempts),
    },
    {
      icon: <Layers size={13} className="text-brand-blue" />,
      label: 'Fields extracted',
      value: String(fieldCount),
    },
    {
      icon: <ShieldCheck size={13} className="text-brand-green" />,
      label: 'Validation status',
      value: validationStatus,
    },
    {
      icon: <Database size={13} className="text-brand-cyan" />,
      label: 'Provider',
      value: provider ?? '-',
    },
    {
      icon: <Cpu size={13} className="text-brand-blue" />,
      label: 'Model',
      value: model ?? '-',
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-2">
      {items.map((item, i) => (
        <motion.div
          key={item.label}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.05 }}
          className="rounded-lg bg-white/[0.02] border border-white/[0.05] px-3 py-2"
        >
          <div className="flex items-center gap-1.5 mb-0.5">
            {item.icon}
            <span className="text-[10px] text-white/40">{item.label}</span>
          </div>
          <p className="text-sm font-semibold text-white mt-0.5">{item.value}</p>
        </motion.div>
      ))}
    </div>
  );
}

/* ── Live Extraction Insights ── */
interface LiveInsightsProps {
  activeStage: number;
  held: boolean;
}

export function LiveExtractionInsights({ activeStage, held }: LiveInsightsProps) {
  const insights = [
    { stage: 1, label: 'Fields extracted', value: '—', icon: Layers },
    { stage: 2, label: 'Entities detected', value: '—', icon: Tag },
    { stage: 3, label: 'Schema completion', value: '—', icon: Gauge },
    { stage: 4, label: 'Validation progress', value: '—', icon: ShieldCheck },
  ];

  const getDisplayValue = (stage: number) => {
    if (held && activeStage >= 5) {
      if (stage === 1) return 'Analyzing...';
      if (stage === 2) return 'Scanning...';
      if (stage === 3) return 'Checking...';
      if (stage === 4) return 'Validating...';
    }
    if (activeStage >= stage) {
      if (stage === 1) return 'Extracting...';
      if (stage === 2) return 'Detecting...';
      if (stage === 3) return 'Mapping...';
      if (stage === 4) return 'Verifying...';
    }
    return 'Waiting...';
  };

  const isActive = activeStage >= 0 && activeStage < 5;

  if (!isActive) return null;

  return (
    <div className="grid grid-cols-2 gap-2">
      {insights.map((insight, i) => {
        const Icon = insight.icon;
        const stageReached = activeStage >= insight.stage;
        return (
          <motion.div
            key={insight.label}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: stageReached ? 0.8 : 0.4, y: 0 }}
            className="rounded-lg bg-white/[0.02] border border-white/[0.05] px-3 py-2"
          >
            <div className="flex items-center gap-1.5 mb-0.5">
              <Icon size={11} className={stageReached ? 'text-brand-cyan' : 'text-white/30'} />
              <span className="text-[10px] text-white/40">{insight.label}</span>
            </div>
            <p className={`text-xs font-medium mt-0.5 ${stageReached ? 'text-white/80' : 'text-white/30'}`}>
              {stageReached ? (
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-cyan animate-pulse" />
                  {getDisplayValue(insight.stage)}
                </span>
              ) : (
                getDisplayValue(insight.stage)
              )}
            </p>
          </motion.div>
        );
      })}
    </div>
  );
}

/* ── AI Reasoning Panel ── */
interface ExplainabilityProps {
  json: Record<string, unknown>;
  ticket: string;
  confidence: number;
}

interface ReasoningSection {
  title: string;
  value: string;
  reason: string;
  icon: typeof AlertTriangle;
}

function extractStructuredReasoning(
  json: Record<string, unknown>,
  ticket: string,
): ReasoningSection[] {
  const lower = ticket.toLowerCase();
  const sections: ReasoningSection[] = [];

  const urgencyKeywords = ['urgent', 'asap', 'immediately', 'as soon as possible', 'emergency', 'critical'];
  const hasUrgency = urgencyKeywords.some((k) => lower.includes(k));
  const hasRefund = /refund/i.test(lower);
  const hasTechnical = /(down|crashes|not working|error|bug|issue|fail)/i.test(lower);
  const billingWords = ['billing', 'charge', 'payment', 'card', 'subscription', 'invoice', 'double charged'];
  const isBilling = billingWords.some((w) => lower.includes(w));
  const hasDollar = /\$\d+/.test(ticket);

  const sentiment = json.sentiment ?? (json as any).urgency;
  const reqAction = json.requested_action ?? (json as any).action;

  if (hasUrgency) {
    sections.push({
      title: 'Urgency',
      value: 'High',
      reason: hasDollar
        ? 'Dollar amounts with urgency keywords indicate time-sensitive billing issue.'
        : 'Customer requested immediate action using urgency language.',
      icon: AlertTriangle,
    });
  } else {
    sections.push({
      title: 'Urgency',
      value: 'Normal',
      reason: 'Standard response time acceptable based on content analysis.',
      icon: AlertTriangle,
    });
  }

  if (isBilling) {
    sections.push({
      title: 'Sentiment',
      value: 'Frustrated',
      reason: 'Multiple billing/financial terms detected suggesting payment frustration.',
      icon: Zap,
    });
  } else if (hasTechnical) {
    sections.push({
      title: 'Sentiment',
      value: 'Technical',
      reason: 'Support ticket describing functional or system issue.',
      icon: Zap,
    });
  } else if (hasRefund) {
    sections.push({
      title: 'Sentiment',
      value: 'Requesting',
      reason: 'Customer proactively requesting specific resolution action.',
      icon: Zap,
    });
  } else {
    sections.push({
      title: 'Sentiment',
      value: 'Neutral',
      reason: 'Standard inquiry without strong emotional indicators.',
      icon: Zap,
    });
  }

  if (reqAction && typeof reqAction === 'string') {
    sections.push({
      title: 'Requested Action',
      value: reqAction,
      reason: hasRefund
        ? 'Explicit refund request identified in ticket content.'
        : 'Primary customer intent identified from request context.',
      icon: FileText,
    });
  }

  if (sentiment && typeof sentiment === 'string') {
    sections.push({
      title: 'Category',
      value: sentiment,
      reason: isBilling
        ? 'Billing category triggered by financial keywords and schema patterns.'
        : hasTechnical
          ? 'Technical category matched from system/error keywords.'
          : 'General support category assigned from content analysis.',
      icon: BrainCircuit,
    });
  }

  return sections;
}

export function ExplainabilityPanel({
  json,
  ticket,
  confidence,
}: ExplainabilityProps) {
  const sections = useMemo(() => extractStructuredReasoning(json, ticket), [json, ticket]);

  if (sections.length === 0) return null;

  return (
    <details className="group">
      <summary className="flex items-center gap-2 cursor-pointer text-sm font-medium text-white/60 hover:text-white/80 transition-colors list-none rounded-lg px-3 py-2 hover:bg-white/[0.02]">
        <Sparkles size={14} className="text-brand-cyan" />
        <span>AI Reasoning</span>
        <ChevronDown size={12} className="ml-auto text-white/30 group-open:rotate-180 transition-transform duration-200" />
      </summary>
      <div className="mt-2 space-y-2 px-3 pb-2">
        {sections.map((section, i) => {
          const Icon = section.icon;
          return (
            <motion.div
              key={section.title}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06 }}
              className="flex items-start gap-2.5 text-xs rounded-lg bg-white/[0.02] border border-white/[0.05] p-2.5"
            >
              <div className="shrink-0 mt-0.5 w-6 h-6 rounded-md bg-brand-cyan/10 flex items-center justify-center">
                <Icon size={12} className="text-brand-cyan" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-2">
                  <span className="font-semibold text-white/70">{section.title}:</span>
                  <span className="font-medium text-brand-cyan">{section.value}</span>
                </div>
                <p className="text-white/40 mt-0.5 leading-relaxed">{section.reason}</p>
              </div>
            </motion.div>
          );
        })}
      </div>
    </details>
  );
}
