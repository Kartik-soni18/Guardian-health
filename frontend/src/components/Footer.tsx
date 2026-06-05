import { AlertTriangle } from 'lucide-react';

export const AI_DISCLAIMER =
  'This is an AI assistant. Do not treat its responses as medical advice — always consult a qualified healthcare provider.';

export function Footer() {
  return (
    <footer className="shrink-0 border-t border-red-900/60 bg-red-950">
      <div className="mx-auto flex max-w-7xl items-center justify-center gap-2.5 px-4 py-2.5 sm:px-6">
        <AlertTriangle className="h-4 w-4 shrink-0 text-red-400" aria-hidden />
        <p className="text-center text-xs font-medium leading-snug text-red-200 sm:text-sm">
          {AI_DISCLAIMER}
        </p>
      </div>
    </footer>
  );
}
