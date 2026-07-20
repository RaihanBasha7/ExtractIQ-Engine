import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from './api';
import type { ExtractionResult } from '../types';

const STAGE_DURATIONS = [400, 700, 1000, 500, 800];

export type RunState = 'idle' | 'running' | 'done' | 'error';

export function useExtraction() {
  const [state, setState] = useState<RunState>('idle');
  const [activeStage, setActiveStage] = useState(-1);
  const [inRepair, setInRepair] = useState(false);
  const [held, setHeld] = useState(false);
  const [apiReady, setApiReady] = useState(false);
  const [result, setResult] = useState<ExtractionResult | null>(null);
  const [error, setError] = useState(false);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const mountedRef = useRef(true);
  const runningRef = useRef(false);
  const pendingResultRef = useRef<ExtractionResult | null>(null);
  const apiReadyRef = useRef(false);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      timers.current.forEach(clearTimeout);
      timers.current = [];
    };
  }, []);

  const clearTimers = useCallback(() => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
  }, []);

  const doFinish = useCallback(() => {
    if (!mountedRef.current || !pendingResultRef.current) return;
    clearTimers();
    setActiveStage(5);
    setInRepair(false);
    setHeld(false);
    setResult(pendingResultRef.current);
    setState('done');
  }, [clearTimers]);

  // When both held + apiReady are true, finish immediately
  useEffect(() => {
    if (held && apiReady && pendingResultRef.current) {
      doFinish();
    }
  }, [held, apiReady, doFinish]);

  const run = useCallback(
    async (ticket: string) => {
      if (!ticket.trim() || runningRef.current) return;
      runningRef.current = true;
      clearTimers();
      setState('running');
      setResult(null);
      setError(false);
      setActiveStage(0);
      setInRepair(false);
      setHeld(false);
      setApiReady(false);
      apiReadyRef.current = false;
      pendingResultRef.current = null;

      const requestPromise = api.extract(ticket);

      let acc = 0;
      const stageTimers: ReturnType<typeof setTimeout>[] = [];
      STAGE_DURATIONS.forEach((d, i) => {
        acc += d;
        const stageIndex = i + 1;
        const t = setTimeout(() => {
          if (!mountedRef.current) return;
          setActiveStage(stageIndex);
          if (stageIndex === 4) setInRepair(true);
          if (stageIndex === 5) {
            setInRepair(false);
            // Use ref to avoid stale closure
            if (apiReadyRef.current) {
              doFinish();
            } else {
              setHeld(true);
            }
          }
        }, acc);
        stageTimers.push(t);
      });
      timers.current = stageTimers;

      try {
        const res = await requestPromise;
        if (!mountedRef.current) { runningRef.current = false; return; }
        pendingResultRef.current = res;
        apiReadyRef.current = true;
        setApiReady(true);
      } catch (err) {
        console.error('[useExtraction] extraction failed:', err);
        if (!mountedRef.current) { runningRef.current = false; return; }
        clearTimers();
        setActiveStage(-1);
        setHeld(false);
        setError(true);
        setState('error');
      }
      runningRef.current = false;
    },
    [doFinish],
  );

  const reset = useCallback(() => {
    clearTimers();
    runningRef.current = false;
    setState('idle');
    setActiveStage(-1);
    setInRepair(false);
    setHeld(false);
    setApiReady(false);
    setResult(null);
    setError(false);
    apiReadyRef.current = false;
    pendingResultRef.current = null;
  }, [clearTimers]);

  return { state, activeStage, inRepair, held, result, error, run, reset };
}
