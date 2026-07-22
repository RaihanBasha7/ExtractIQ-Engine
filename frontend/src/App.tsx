import { lazy, Suspense } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { SettingsProvider } from './lib/settingsContext';
import { ExtractionProvider } from './lib/extractionContext';
import { Layout } from './components/Layout';

const Dashboard = lazy(() => import('./pages/Dashboard').then((m) => ({ default: m.Dashboard })));
const ExtractTicket = lazy(() => import('./pages/ExtractTicket').then((m) => ({ default: m.ExtractTicket })));
const BatchExtract = lazy(() => import('./pages/BatchExtract').then((m) => ({ default: m.BatchExtract })));
const Analytics = lazy(() => import('./pages/Analytics').then((m) => ({ default: m.Analytics })));
const Health = lazy(() => import('./pages/Health').then((m) => ({ default: m.Health })));
const History = lazy(() => import('./pages/History').then((m) => ({ default: m.History })));
const SettingsPage = lazy(() => import('./pages/SettingsPage').then((m) => ({ default: m.SettingsPage })));
const Playground = lazy(() => import('./pages/Playground').then((m) => ({ default: m.Playground })));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30000, refetchOnWindowFocus: false, retry: 1 },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <SettingsProvider>
        <BrowserRouter>
          <ExtractionProvider>
          <Layout>
            <Suspense fallback={
              <div className="flex items-center justify-center h-64" role="status" aria-label="Loading page">
                <div className="w-8 h-8 border-2 border-brand-blue/30 border-t-brand-blue rounded-full animate-spin" />
                <span className="sr-only">Loading page...</span>
              </div>
            }>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/extract" element={<ExtractTicket />} />
                <Route path="/batch" element={<BatchExtract />} />
                <Route path="/playground" element={<Playground />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/health" element={<Health />} />
                <Route path="/history" element={<History />} />
                <Route path="/settings" element={<SettingsPage />} />
              </Routes>
            </Suspense>
          </Layout>
          </ExtractionProvider>
        </BrowserRouter>
      </SettingsProvider>
    </QueryClientProvider>
  );
}
