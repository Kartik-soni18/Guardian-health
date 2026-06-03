import { useState, useRef, useCallback, KeyboardEvent } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SymptomInputProps {
  onSend: (content: string) => void;
  placeholder?: string;
  isLoading?: boolean;
  minRows?: number;
  showSuggestedPrompts?: boolean;
  className?: string;
}

export function SymptomInput({
  onSend,
  placeholder = "Describe your symptoms...",
  isLoading = false,
  minRows = 1,
  className,
}: SymptomInputProps) {
  const [content, setContent] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const maxHeight = 200;
      textarea.style.height = `${Math.min(textarea.scrollHeight, maxHeight)}px`;
    }
  }, []);

  const handleSend = useCallback(() => {
    const trimmed = content.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setContent('');
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
    }
  }, [content, isLoading, onSend]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setContent(e.target.value);
      requestAnimationFrame(adjustHeight);
    },
    [adjustHeight]
  );

  const isEmpty = content.trim().length === 0;

  return (
    <div className={cn('relative', className)}>
      <div className="flex items-end gap-2 rounded-xl border border-gray-300 bg-white p-2 shadow-sm transition-all focus-within:border-primary-500 focus-within:ring-2 focus-within:ring-primary-200 dark:border-gray-700 dark:bg-gray-800 dark:focus-within:border-primary-400 dark:focus-within:ring-primary-900">
        <textarea
          ref={textareaRef}
          value={content}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          rows={minRows}
          disabled={isLoading}
          className="max-h-[200px] w-full resize-none bg-transparent px-2 py-2 text-sm text-gray-900 outline-none placeholder:text-gray-400 disabled:opacity-50 dark:text-white"
          placeholder={placeholder}
        />
        <button
          onClick={handleSend}
          disabled={isEmpty || isLoading}
          className={cn(
            'mb-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-all',
            isEmpty || isLoading
              ? 'text-gray-300 dark:text-gray-600'
              : 'bg-primary-600 text-white shadow-sm hover:bg-primary-700 active:scale-95'
          )}
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </button>
      </div>
    </div>
  );
}
