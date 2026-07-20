import { useState, useEffect, type ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { Navbar } from './Navbar';
import { AnimatedBackground } from './AnimatedBackground';
import { useSettings } from '../lib/settings';

export function Layout({ children }: { children: ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const { animations } = useSettings();

  useEffect(() => {
    const main = document.getElementById('layout-main');
    if (!main) return;
    let ticking = false;
    const onScroll = () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        setScrolled(main.scrollTop > 8);
        ticking = false;
      });
    };
    main.addEventListener('scroll', onScroll, { passive: true });
    return () => main.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <div className="flex min-h-screen">
      {animations && <AnimatedBackground />}
      <Sidebar open={sidebarOpen} />
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden backdrop-blur-sm"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      <div className="flex-1 min-w-0 flex flex-col h-screen overflow-hidden">
        <div className="sticky top-0 z-20 px-3 lg:px-5 pt-3 lg:pt-4 pb-2">
          <Navbar onMenu={() => setSidebarOpen((v) => !v)} scrolled={scrolled} />
        </div>
        <main
          id="layout-main"
          className="flex-1 overflow-y-auto p-3 lg:p-6 opacity-0 animate-fade-in"
          style={{ animation: 'fadeIn 0.4s cubic-bezier(0.22, 1, 0.36, 1) forwards' }}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
