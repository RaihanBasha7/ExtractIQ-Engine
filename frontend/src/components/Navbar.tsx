import { memo, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Search,
  Sun,
  Moon,
  Menu,
  ChevronDown,
  Sparkles,
} from 'lucide-react';
import { api } from '../lib/api';
import { StatusDot } from './StatusDot';
import { useSettings } from '../lib/settings';
import { Logo } from './Logo';

interface NavbarProps {
  onMenu: () => void;
  scrolled: boolean;
}

export const Navbar = memo(function Navbar({ onMenu, scrolled }: NavbarProps) {
  const healthQ = useQuery({ queryKey: ['health'], queryFn: () => api.health(), refetchInterval: 15000 });
  const { darkMode, toggleDark } = useSettings();
  const headerRef = useRef<HTMLDivElement>(null);

  return (
    <header className="relative z-20" ref={headerRef}>
      <div
        className={`rounded-2xl border px-4 py-2.5 flex items-center gap-2.5 transition-all duration-500 ease-out ${
          scrolled
            ? 'bg-[rgba(13,19,34,0.78)] backdrop-blur-2xl border-[rgba(255,255,255,0.14)] shadow-[0_12px_40px_-12px_rgba(0,0,0,0.7),0_0_0_1px_rgba(255,255,255,0.04)]'
            : 'bg-[rgba(13,19,34,0.35)] backdrop-blur-xl border-[rgba(255,255,255,0.08)] shadow-[0_8px_30px_-14px_rgba(0,0,0,0.5)]'
        } dark:bg-[rgba(13,19,34,0.78)] dark:backdrop-blur-2xl dark:border-[rgba(255,255,255,0.14)]`}
      >
        <button
          onClick={onMenu}
          className="lg:hidden p-2 -ml-1 rounded-lg hover:bg-white/[0.06] text-white/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue/50"
          aria-label="Toggle navigation"
        >
          <Menu size={18} />
        </button>

        <div className="flex items-center gap-2.5">
          <Logo size={28} />
          <span className="hidden sm:block text-sm font-semibold text-white tracking-tight">
            ExtractIQ <span className="text-white/40">Engine</span>
          </span>
        </div>

        <span className="hidden md:inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium text-white/65 bg-white/[0.04] border border-white/[0.08]">
          <Sparkles size={11} className="text-brand-cyan" />
          AI Structured Extraction
        </span>

        <div className="flex-1" />

        <div className="hidden md:flex items-center gap-2 rounded-xl bg-white/[0.03] border border-white/[0.06] px-3 py-1.5 w-56 lg:w-64 focus-within:border-brand-blue/40 transition-colors">
          <Search size={14} className="text-white/40" />
          <input
            placeholder="Search extractions&hellip;"
            aria-label="Search extractions"
            className="bg-transparent text-sm text-white/80 placeholder:text-white/30 outline-none w-full"
          />
          <kbd className="text-[10px] text-white/30 border border-white/10 rounded px-1.5 py-0.5">&larrk;K</kbd>
        </div>

        <div className="hidden sm:flex items-center gap-2 rounded-xl bg-white/[0.03] border border-white/[0.06] px-3 py-1.5">
          <StatusDot state={healthQ.data?.status ?? 'unknown'} size={8} />
          <span className="text-xs font-medium text-white/70">
            {healthQ.data?.status ?? 'checking'}
          </span>
        </div>

        <button
          onClick={toggleDark}
          className="p-2 rounded-xl bg-white/[0.03] border border-white/[0.06] text-white/70 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue/50 transition-colors"
          title={darkMode ? 'Switch to light theme' : 'Switch to dark theme'}
          aria-label={darkMode ? 'Switch to light theme' : 'Switch to dark theme'}
        >
          {darkMode ? <Sun size={16} /> : <Moon size={16} />}
        </button>

        <button
          className="flex items-center gap-2 rounded-xl bg-white/[0.03] border border-white/[0.06] pl-1.5 pr-2 py-1.5 hover:bg-white/[0.06] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue/50"
          aria-label="Account menu"
        >
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-brand-blue to-brand-cyan flex items-center justify-center text-xs font-bold text-white">
            EX
          </div>
          <ChevronDown size={14} className="text-white/40 hidden sm:block" />
        </button>
      </div>
    </header>
  );
});
