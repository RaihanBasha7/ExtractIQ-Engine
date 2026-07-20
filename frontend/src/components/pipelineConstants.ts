import { Inbox, Upload, Brush, BrainCircuit, Braces, ShieldCheck, Recycle, CheckCircle2, Sparkles } from 'lucide-react';
import type { PipelineStage } from '../types';

export const PIPELINE_STAGES: PipelineStage[] = [
  { id: 'upload', label: 'Uploading', description: 'Receiving ticket payload', status: 'pending' },
  { id: 'preprocess', label: 'Preprocessing', description: 'Cleaning & normalizing text', status: 'pending' },
  { id: 'understand', label: 'AI Understanding', description: 'LLM analyzing intent & entities', status: 'pending' },
  { id: 'validate', label: 'Schema Validation', description: 'Checking against schema v1.2.0', status: 'pending' },
  { id: 'repair', label: 'Repair Loop', description: 'Patching schema violations', status: 'pending' },
  { id: 'generate', label: 'Generating JSON', description: 'Producing final structured output', status: 'pending' },
  { id: 'done', label: 'Completed', description: 'Guaranteed JSON ready', status: 'pending' },
];

export const STAGE_ICONS: Record<string, typeof Inbox> = {
  upload: Upload,
  preprocess: Brush,
  understand: BrainCircuit,
  validate: ShieldCheck,
  repair: Recycle,
  generate: Braces,
  done: Sparkles,
};

export const NODES = [
  { id: 'ticket', label: 'Input', icon: Inbox },
  { id: 'preprocess', label: 'Preprocessing', icon: Brush },
  { id: 'llm', label: 'LLM Extraction', icon: BrainCircuit },
  { id: 'structured', label: 'Structured Output', icon: Braces },
  { id: 'validation', label: 'Validation', icon: ShieldCheck },
  { id: 'repair', label: 'Repair Loop', icon: Recycle },
  { id: 'final', label: 'Guaranteed JSON', icon: CheckCircle2 },
] as const;

export function nodeActiveAt(activeIndex: number): string[] {
  const map: Record<number, string[]> = {
    0: ['ticket'],
    1: ['preprocess'],
    2: ['llm'],
    3: ['validation'],
    4: ['repair', 'validation'],
    5: ['structured'],
    6: ['final'],
  };
  return map[activeIndex] ?? [];
}