import { AlertTriangle, RefreshCw } from 'lucide-react';
import { motion } from 'framer-motion';

interface ErrorCardProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export function ErrorCard({
  title = 'Something went wrong',
  message = 'We could not reach the ExtractIQ service. Please try again.',
  onRetry,
}: ErrorCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass-card p-8 flex flex-col items-center text-center max-w-md mx-auto"
    >
      <div className="w-12 h-12 rounded-2xl bg-red-500/15 border border-red-500/30 flex items-center justify-center mb-4">
        <AlertTriangle className="text-red-400" size={22} />
      </div>
      <h3 className="text-lg font-semibold text-white">{title}</h3>
      <p className="mt-2 text-sm text-white/55 leading-relaxed">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn-primary mt-5">
          <RefreshCw size={15} /> Retry
        </button>
      )}
    </motion.div>
  );
}
