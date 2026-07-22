import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { SettingsProvider } from './lib/settingsContext';
import { ExtractionProvider } from './lib/extractionContext';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { ExtractTicket } from './pages/ExtractTicket';
import { BatchExtract } from './pages/BatchExtract';
import { Analytics } from './pages/Analytics';
import { Health } from './pages/Health';
import { History } from './pages/History';
import { SettingsPage } from './pages/SettingsPage';
import { Playground } from './pages/Playground';

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
          </Layout>
          </ExtractionProvider>
        </BrowserRouter>
      </SettingsProvider>
    </QueryClientProvider>
  );
}
