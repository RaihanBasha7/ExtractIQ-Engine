import { useState, useCallback } from 'react';
import { Check, Copy, Save, ChevronDown, ChevronRight } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface JsonBlockProps {
  data: unknown;
  maxHeight?: string;
  showDownload?: boolean;
}

export function JsonBlock({ data, maxHeight = '400px', showDownload = true }: JsonBlockProps) {
  const [copied, setCopied] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const json = JSON.stringify(data, null, 2);

  const copy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(json);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch { /* ignore */ }
  }, [json]);

  const download = useCallback(() => {
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'extraction.json';
    a.click();
    URL.revokeObjectURL(url);
  }, [json]);

  return (
    <div className="relative group">
      <div className="absolute top-2 right-2 z-10 flex items-center gap-1.5">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="inline-flex items-center gap-1 rounded-lg bg-white/[0.06] hover:bg-white/[0.12] border border-white/[0.08] px-2 py-1.5 text-xs font-medium text-white/70 hover:text-white transition-all"
          title={collapsed ? 'Expand' : 'Collapse'}
        >
          {collapsed ? <ChevronRight size={12} /> : <ChevronDown size={12} />}
        </button>
        {showDownload && (
          <button
            onClick={download}
            className="inline-flex items-center gap-1 rounded-lg bg-white/[0.06] hover:bg-white/[0.12] border border-white/[0.08] px-2 py-1.5 text-xs font-medium text-white/70 hover:text-white transition-all"
            title="Download JSON"
          >
            <Save size={12} />
          </button>
        )}
        <button
          onClick={copy}
          className="inline-flex items-center gap-1 rounded-lg bg-white/[0.06] hover:bg-white/[0.12] border border-white/[0.08] px-2 py-1.5 text-xs font-medium text-white/70 hover:text-white transition-all"
        >
          {copied ? <Check size={12} className="text-brand-green" /> : <Copy size={12} />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <div
        className={`rounded-xl bg-[#0a0e1a] border border-white/[0.06] transition-all duration-300 ease-out ${
          collapsed ? 'max-h-[52px] overflow-hidden' : ''
        }`}
        style={collapsed ? {} : { maxHeight, overflow: 'auto' }}
      >
        <SyntaxHighlighter
          language="json"
          style={vscDarkPlus}
          customStyle={{
            margin: 0,
            padding: '16px 18px',
            background: 'transparent',
            fontSize: '12.5px',
            lineHeight: '1.6',
          }}
          codeTagProps={{ style: { fontFamily: 'JetBrains Mono, monospace' } }}
        >
          {json}
        </SyntaxHighlighter>
      </div>
    </div>
  );
}
