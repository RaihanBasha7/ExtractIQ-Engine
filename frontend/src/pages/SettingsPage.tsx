import { useState } from 'react';
import { motion } from 'framer-motion';
import { Sun, Moon, Sparkles, Recycle, Link2, Info, Check } from 'lucide-react';
import { GlassCard } from '../components/GlassCard';
import { useSettings } from '../lib/settings';

export function SettingsPage() {
  const {
    darkMode,
    toggleDark,
    animations,
    toggleAnimations,
    showRepairAttempts,
    toggleShowRepairAttempts,
    apiBaseUrl,
    setApiBaseUrl,
  } = useSettings();
  const [urlInput, setUrlInput] = useState(apiBaseUrl);
  const [saved, setSaved] = useState(false);

  const saveUrl = () => {
    setApiBaseUrl(urlInput.trim());
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">Settings</h1>
        <p className="mt-1.5 text-sm text-white/50">Personalize ExtractIQ Engine.</p>
      </div>

      <GlassCard hover={false} className="p-5">
        <h3 className="text-sm font-semibold text-white mb-4">Appearance</h3>
        <Toggle
          icon={darkMode ? <Moon size={15} /> : <Sun size={15} />}
          label="Dark mode"
          desc="Use the dark theme across the app."
          value={darkMode}
          onChange={toggleDark}
        />
        <div className="h-px bg-white/[0.05] my-4" />
        <Toggle
          icon={<Sparkles size={15} />}
          label="Animations"
          desc="Enable particles, glows, and motion transitions."
          value={animations}
          onChange={toggleAnimations}
        />
      </GlassCard>

      <GlassCard hover={false} className="p-5">
        <h3 className="text-sm font-semibold text-white mb-4">Extraction</h3>
        <Toggle
          icon={<Recycle size={15} />}
          label="Show repair attempts"
          desc="Display the repair loop history in extraction output."
          value={showRepairAttempts}
          onChange={toggleShowRepairAttempts}
        />
      </GlassCard>

      <GlassCard hover={false} className="p-5">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Link2 size={15} className="text-brand-cyan" /> Backend endpoint
        </h3>
        <p className="text-xs text-white/40 mb-3">
          Base URL of the ExtractIQ API. Leave blank to use the same origin. Changes apply to new requests.
        </p>
        <div className="flex gap-2">
          <input
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            placeholder="https://api.extractiq.example.com"
            aria-label="Backend endpoint URL"
            className="flex-1 rounded-xl bg-[#0a0e1a] border border-white/[0.06] px-3 py-2.5 text-sm text-white/85 placeholder:text-white/25 outline-none focus:border-brand-blue/40 font-mono"
          />
          <button onClick={saveUrl} className="btn-primary">
            {saved ? <Check size={15} className="text-white" /> : null}
            {saved ? 'Saved' : 'Save'}
          </button>
        </div>
      </GlassCard>

      <GlassCard hover={false} className="p-5">
        <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
          <Info size={15} className="text-brand-cyan" /> About
        </h3>
        <p className="text-sm text-white/55 leading-relaxed">
          ExtractIQ Engine is a production-ready AI structured extraction service with a
          model-driven repair loop. It transforms noisy customer tickets into guaranteed,
          schema-valid JSON through a transparent pipeline: preprocessing → LLM extraction →
          validation → repair → guaranteed output.
        </p>
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          className="mt-4 flex flex-wrap gap-2"
        >
          {['React', 'Vite', 'Tailwind', 'Framer Motion', 'Recharts', 'React Query'].map((t) => (
            <span key={t} className="chip bg-white/[0.04] border border-white/[0.08] text-white/55">
              {t}
            </span>
          ))}
        </motion.div>
      </GlassCard>
    </div>
  );
}

function Toggle({
  icon,
  label,
  desc,
  value,
  onChange,
}: {
  icon: React.ReactNode;
  label: string;
  desc: string;
  value: boolean;
  onChange: () => void;
}) {
  return (
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-xl bg-white/[0.04] border border-white/[0.06] flex items-center justify-center text-brand-cyan">
        {icon}
      </div>
      <div className="flex-1">
        <p className="text-sm font-medium text-white">{label}</p>
        <p className="text-xs text-white/40">{desc}</p>
      </div>
      <button
        onClick={onChange}
        aria-label={label}
        aria-pressed={value}
        className={`relative w-11 h-6 rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue/50 ${
          value ? 'bg-brand-blue' : 'bg-white/[0.08]'
        }`}
      >
        <motion.span
          layout
          transition={{ type: 'spring', stiffness: 500, damping: 30 }}
          className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow-md ${value ? 'left-[22px]' : 'left-0.5'}`}
        />
      </button>
    </div>
  );
}
