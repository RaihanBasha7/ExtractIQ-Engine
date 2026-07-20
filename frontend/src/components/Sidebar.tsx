import { memo, useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Layers,
  BarChart3,
  HeartPulse,
  History,
  Settings,
  Sparkles,
  ChevronRight,
  Boxes,
  type LucideIcon,
} from 'lucide-react';
import { Logo } from './Logo';

interface LeafItem {
  to: string;
  label: string;
  desc: string;
  icon: LucideIcon;
  end?: boolean;
}

interface Group {
  id: string;
  label: string;
  icon: LucideIcon;
  items: LeafItem[];
}

const GROUPS: Group[] = [
  {
    id: 'extraction',
    label: 'Extraction',
    icon: Boxes,
    items: [
      { to: '/extract', label: 'Single Extract', desc: 'Single AI extraction', icon: FileText },
      { to: '/batch', label: 'Batch Extract', desc: 'Bulk processing', icon: Layers },
    ],
  },
  {
    id: 'monitoring',
    label: 'Monitoring',
    icon: BarChart3,
    items: [
      { to: '/analytics', label: 'Analytics', desc: 'Performance insights', icon: BarChart3 },
      { to: '/health', label: 'Health', desc: 'System monitoring', icon: HeartPulse },
      { to: '/history', label: 'History', desc: 'Previous extractions', icon: History },
    ],
  },
];

const TOP_NAV: LeafItem[] = [
  { to: '/', label: 'Dashboard', desc: 'Overview and live metrics', icon: LayoutDashboard, end: true },
];

const BOTTOM_NAV: LeafItem[] = [
  { to: '/playground', label: 'AI Playground', desc: 'Visualize the pipeline', icon: Sparkles },
  { to: '/settings', label: 'Settings', desc: 'Application preferences', icon: Settings },
];

interface SidebarProps {
  open: boolean;
}

export const Sidebar = memo(function Sidebar({ open }: SidebarProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>(() => {
    try {
      const stored = localStorage.getItem('extractiq.nav');
      if (stored) return JSON.parse(stored);
    } catch { /* ignore */ }
    return { extraction: true, monitoring: true };
  });

  const toggle = (id: string) =>
    setExpanded((prev) => {
      const next = { ...prev, [id]: !prev[id] };
      try { localStorage.setItem('extractiq.nav', JSON.stringify(next)); } catch { /* ignore */ }
      return next;
    });

  return (
    <aside
      className={`fixed lg:sticky top-0 left-0 z-40 h-screen w-72 shrink-0 transition-transform duration-300 ${
        open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      }`}
    >
      <div className="h-full m-3 mr-0 lg:mr-3 glass-card p-4 flex flex-col overflow-hidden">
        <div className="flex items-center gap-3 px-2 py-2 mb-3">
          <Logo size={36} />
          <div className="leading-tight">
            <p className="text-sm font-bold text-white tracking-tight">ExtractIQ</p>
            <p className="text-[10px] uppercase tracking-[0.18em] text-white/40">Engine</p>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto no-scrollbar -mx-1 px-1 space-y-5" aria-label="Primary">
          <div className="space-y-1">
            {TOP_NAV.map((item) => (
              <NavLeaf key={item.to} item={item} />
            ))}
          </div>

          {GROUPS.map((group) => (
            <div key={group.id}>
              <button
                onClick={() => toggle(group.id)}
                className="flex w-full items-center gap-2 px-2 py-1.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-white/35 hover:text-white/60 transition-colors"
                aria-expanded={expanded[group.id]}
                aria-controls={`group-${group.id}`}
              >
                <group.icon size={12} />
                <span className="flex-1 text-left">{group.label}</span>
                <ChevronRight
                  size={12}
                  className={`transition-transform duration-200 ${
                    expanded[group.id] ? 'rotate-90' : ''
                  }`}
                />
              </button>
              <div
                id={`group-${group.id}`}
                className={`overflow-hidden transition-all duration-250 ease-out ${
                  expanded[group.id] ? 'max-h-96 opacity-100 mt-1' : 'max-h-0 opacity-0'
                }`}
              >
                <div className="space-y-1">
                  {group.items.map((item) => (
                    <NavLeaf key={item.to} item={item} nested />
                  ))}
                </div>
              </div>
            </div>
          ))}

          <div className="space-y-1">
            {BOTTOM_NAV.map((item) => (
              <NavLeaf key={item.to} item={item} />
            ))}
          </div>
        </nav>

        <div className="mt-3 p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
          <p className="text-[11px] text-white/45 leading-relaxed">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-brand-green mr-1.5 align-middle animate-pulse" />
            All systems operational
          </p>
          <p className="text-[10px] text-white/30 mt-1">v1.4.2 · production</p>
        </div>
      </div>
    </aside>
  );
});

function NavLeaf({ item, nested = false }: { item: LeafItem; nested?: boolean }) {
  return (
    <NavLink
      to={item.to}
      end={item.end}
      className={({ isActive }) =>
        `relative flex items-center gap-3 rounded-xl px-3 ${nested ? 'py-2' : 'py-2.5'} text-sm font-medium transition-all duration-200 group ${
          isActive
            ? 'text-white bg-white/[0.04]'
            : 'text-white/55 hover:text-white hover:bg-white/[0.03]'
        }`
      }
    >
      {({ isActive }) => (
        <>
          {isActive && (
            <span className="absolute inset-0 rounded-xl bg-gradient-to-r from-brand-blue/15 to-brand-cyan/[0.06] border border-white/[0.08]" />
          )}
          {isActive && (
            <span className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-[3px] rounded-full bg-gradient-to-b from-brand-blue to-brand-cyan" />
          )}
          <span
            className={`relative z-10 flex items-center justify-center w-8 h-8 rounded-lg transition-all ${
              isActive
                ? 'bg-gradient-to-br from-brand-blue/20 to-brand-cyan/10 text-brand-cyan'
                : 'text-white/45 group-hover:text-white/80'
            }`}
          >
            <item.icon size={16} />
          </span>
          <span className="relative z-10 flex-1 min-w-0">
            <span className="block text-[13px] font-medium leading-tight">{item.label}</span>
            <span className="block text-[10.5px] text-white/35 leading-tight mt-0.5 truncate">
              {item.desc}
            </span>
          </span>
        </>
      )}
    </NavLink>
  );
}
