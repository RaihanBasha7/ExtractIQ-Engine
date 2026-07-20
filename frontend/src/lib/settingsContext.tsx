import { createContext, useEffect, useState, type ReactNode } from 'react';
import { getApiBase, setApiBase } from './api';

interface Settings {
  darkMode: boolean;
  animations: boolean;
  showRepairAttempts: boolean;
  apiBaseUrl: string;
  toggleDark: () => void;
  toggleAnimations: () => void;
  toggleShowRepairAttempts: () => void;
  setApiBaseUrl: (url: string) => void;
}

const SettingsContext = createContext<Settings | null>(null);

export { SettingsContext };

const STORAGE_KEYS = {
  darkMode: 'extractiq.darkMode',
  animations: 'extractiq.animations',
  showRepairAttempts: 'extractiq.showRepairAttempts',
} as const;

function loadBoolean(key: string, fallback: boolean): boolean {
  try {
    const stored = localStorage.getItem(key);
    if (stored !== null) return stored === 'true';
  } catch { /* ignore */ }
  return fallback;
}

function saveBoolean(key: string, value: boolean) {
  try {
    localStorage.setItem(key, String(value));
  } catch { /* ignore */ }
}

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [darkMode, setDarkMode] = useState(() => loadBoolean(STORAGE_KEYS.darkMode, true));
  const [animations, setAnimations] = useState(() => loadBoolean(STORAGE_KEYS.animations, true));
  const [showRepairAttempts, setShowRepairAttempts] = useState(() => loadBoolean(STORAGE_KEYS.showRepairAttempts, true));
  const [apiBaseUrl, setApiBaseUrlState] = useState<string>(() => getApiBase());

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
    saveBoolean(STORAGE_KEYS.darkMode, darkMode);
  }, [darkMode]);

  useEffect(() => {
    saveBoolean(STORAGE_KEYS.animations, animations);
  }, [animations]);

  useEffect(() => {
    saveBoolean(STORAGE_KEYS.showRepairAttempts, showRepairAttempts);
  }, [showRepairAttempts]);

  return (
    <SettingsContext.Provider
      value={{
        darkMode,
        animations,
        showRepairAttempts,
        apiBaseUrl,
        toggleDark: () => setDarkMode((v) => !v),
        toggleAnimations: () => setAnimations((v) => !v),
        toggleShowRepairAttempts: () => setShowRepairAttempts((v) => !v),
        setApiBaseUrl: (url: string) => {
          setApiBase(url);
          setApiBaseUrlState(getApiBase());
        },
      }}
    >
      {children}
    </SettingsContext.Provider>
  );
}