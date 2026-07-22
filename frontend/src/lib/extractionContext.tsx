import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import type { ExtractionResult } from '../types';
import type { BatchUploadSummary } from './api';

const SINGLE_KEY = 'extractiq_single_result';
const BATCH_KEY = 'extractiq_batch_result';

interface ExtractionContextValue {
  singleResult: ExtractionResult | null;
  setSingleResult: (result: ExtractionResult | null) => void;
  batchResult: BatchUploadSummary | null;
  setBatchResult: (result: BatchUploadSummary | null) => void;
  clearSingle: () => void;
  clearBatch: () => void;
}

const ExtractionCtx = createContext<ExtractionContextValue | null>(null);

export function ExtractionProvider({ children }: { children: ReactNode }) {
  const [singleResult, setSingleResultState] = useState<ExtractionResult | null>(() => {
    try {
      const stored = localStorage.getItem(SINGLE_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const [batchResult, setBatchResultState] = useState<BatchUploadSummary | null>(() => {
    try {
      const stored = localStorage.getItem(BATCH_KEY);
      if (!stored) return null;
      const parsed = JSON.parse(stored);
      return parsed.summary ?? null;
    } catch {
      return null;
    }
  });

  useEffect(() => {
    if (singleResult) {
      localStorage.setItem(SINGLE_KEY, JSON.stringify(singleResult));
    } else {
      localStorage.removeItem(SINGLE_KEY);
    }
  }, [singleResult]);

  useEffect(() => {
    if (batchResult) {
      localStorage.setItem(BATCH_KEY, JSON.stringify({ summary: batchResult }));
    } else {
      localStorage.removeItem(BATCH_KEY);
    }
  }, [batchResult]);

  const setSingleResult = useCallback((result: ExtractionResult | null) => {
    setSingleResultState(result);
  }, []);

  const setBatchResult = useCallback((result: BatchUploadSummary | null) => {
    setBatchResultState(result);
  }, []);

  const clearSingle = useCallback(() => setSingleResultState(null), []);
  const clearBatch = useCallback(() => setBatchResultState(null), []);

  return (
    <ExtractionCtx.Provider value={{ singleResult, setSingleResult, batchResult, setBatchResult, clearSingle, clearBatch }}>
      {children}
    </ExtractionCtx.Provider>
  );
}

export function useExtractionContext() {
  const ctx = useContext(ExtractionCtx);
  if (!ctx) throw new Error('useExtractionContext must be used within ExtractionProvider');
  return ctx;
}
