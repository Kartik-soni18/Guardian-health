import { useState, useCallback } from 'react';
import { format } from 'date-fns';
import { User, Copy, Check, Sparkles } from 'lucide-react';
import { ChatMessage as ChatMessageType } from '@/types';
import { TriageCard } from './TriageCard';

interface ChatMessageProps {
  message: ChatMessageType;
  isLast?: boolean;
  isStreaming?: boolean;
}

export function ChatMessage({ message, isStreaming }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for browsers that don't support clipboard API
      const textArea = document.createElement('textarea');
      textArea.value = message.content;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [message.content]);

  return (
    <div
      className={`group animate-fade-in ${isUser ? 'bg-transparent' : 'bg-white/60 dark:bg-gray-900/40'}`}
    >
      <div className="mx-auto flex max-w-3xl gap-4 px-4 py-5 sm:px-6">
        {/* Avatar */}
        <div className="shrink-0">
          {isUser ? (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-200 dark:bg-gray-700">
              <User className="h-4 w-4 text-gray-600 dark:text-gray-300" />
            </div>
          ) : (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 dark:bg-primary-950">
              <Sparkles className="h-4 w-4 text-primary-600 dark:text-primary-400" />
            </div>
          )}
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1">
          {/* Header */}
          <div className="mb-1 flex items-center gap-2">
            <span className="text-sm font-semibold text-gray-900 dark:text-white">
              {isUser ? 'You' : 'GuardianHealth'}
            </span>
            {message.createdAt && (
              <span className="text-xs text-gray-400 dark:text-gray-600">
                {format(new Date(message.createdAt), 'h:mm a')}
              </span>
            )}
          </div>

          {/* Message Body — hide raw text when structured triage card is shown */}
          {!message.triage && (
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <div className="whitespace-pre-wrap text-sm leading-relaxed text-gray-700 dark:text-gray-300">
                {message.content}
                {isStreaming && (
                  <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse bg-primary-500" />
                )}
              </div>
            </div>
          )}

          {message.triage && (
            <div className="mt-4">
              <TriageCard triage={message.triage} />
            </div>
          )}

          {/* Actions */}
          {!isUser && !isStreaming && (
            <div className="mt-2 flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
              <button
                onClick={handleCopy}
                className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:text-gray-500 dark:hover:bg-gray-800 dark:hover:text-gray-300"
                title="Copy message"
              >
                {copied ? (
                  <>
                    <Check className="h-3 w-3" />
                    Copied
                  </>
                ) : (
                  <>
                    <Copy className="h-3 w-3" />
                    Copy
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
