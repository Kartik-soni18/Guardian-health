import { useRef, useEffect, useCallback } from 'react';
import {
  AlertTriangle,
  RefreshCw,
  Sparkles,
  Flame,
  Thermometer,
  Brain,
  Bone,
} from 'lucide-react';
import { ChatMessage as ChatMessageType, PartialTriageResponse } from '@/types';
import { ChatMessage } from './ChatMessage';
import { SymptomInput } from './SymptomInput';
import { StreamingTriageCard } from './StreamingTriageCard';
import { StreamingFollowUp } from './StreamingFollowUp';

interface ChatInterfaceProps {
  messages: ChatMessageType[];
  isLoading: boolean;
  isStreaming: boolean;
  streamingContent: string;
  streamingTriage: PartialTriageResponse | null;
  statusMessage: string;
  error: string | null;
  onSendMessage: (content: string) => void;
  onStartChat: (content: string) => void;
  chatId: string | null;
}

const suggestedPrompts = [
  { text: 'I have a fever and body aches', icon: Thermometer },
  { text: 'I have a severe headache', icon: Brain },
  { text: 'I burned my hand cooking', icon: Flame },
  { text: 'I twisted my ankle', icon: Bone },
];

const messageRowClass =
  'mx-auto flex w-full max-w-3xl gap-4 px-4 sm:px-6 lg:px-8';

export function ChatInterface({
  messages,
  isLoading,
  isStreaming,
  streamingContent,
  streamingTriage,
  statusMessage,
  error,
  onSendMessage,
  onStartChat,
}: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const hasMessages = messages.length > 0;
  const isFollowUpStream =
    streamingTriage?.responseMode === 'follow_up' ||
    ((streamingTriage?.followUpQuestions?.length ?? 0) > 0 && !streamingTriage?.triageLevel);
  const isTriageReportStream =
    Boolean(streamingTriage) &&
    !isFollowUpStream &&
    (streamingTriage?.responseMode === 'triage_report' ||
      !!streamingTriage?.triageLevel ||
      (streamingTriage?.immediateActions?.length ?? 0) > 0);
  const hasStreamingPreview = isFollowUpStream || isTriageReportStream || Boolean(streamingContent);
  const isTyping = isStreaming && !hasStreamingPreview;

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent, streamingTriage, scrollToBottom]);

  const handleSend = (content: string) => {
    if (!hasMessages) {
      onStartChat(content);
    } else {
      onSendMessage(content);
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* Panel header — aligns with sidebar "Conversations" row */}
      <div className="flex h-14 shrink-0 items-center border-b border-gray-200 px-4 dark:border-gray-800 sm:px-6 lg:px-8">
        <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
          {hasMessages ? 'Conversation' : 'New Conversation'}
        </h2>
      </div>

      {/* Messages Area */}
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto scroll-smooth"
      >
        {!hasMessages && !isLoading ? (
          /* Empty state — top-aligned bot row, same layout as ChatMessage */
          <div className="bg-white/60 py-5 dark:bg-gray-900/40">
            <div className={messageRowClass}>
              <div className="shrink-0">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 dark:bg-primary-950">
                  <Sparkles className="h-4 w-4 text-primary-600 dark:text-primary-400" />
                </div>
              </div>
              <div className="min-w-0 flex-1">
                <div className="mb-1 flex items-center gap-2">
                  <span className="text-sm font-semibold text-gray-900 dark:text-white">
                    GuardianHealth
                  </span>
                </div>
                <p className="text-sm leading-relaxed text-gray-700 dark:text-gray-300">
                  How can I help you today? Describe your symptoms or health concerns
                  and I&apos;ll help assess your condition and suggest next steps.
                </p>

                <div className="mt-5 grid gap-3 sm:grid-cols-2">
                  {suggestedPrompts.map((prompt) => {
                    const Icon = prompt.icon;
                    return (
                      <button
                        key={prompt.text}
                        onClick={() => handleSend(prompt.text)}
                        className="group flex items-center gap-3 rounded-xl border border-gray-200/80 bg-white p-3.5 text-left shadow-sm transition-all hover:-translate-y-0.5 hover:border-primary-300 hover:shadow-md dark:border-gray-800 dark:bg-gray-900/80 dark:hover:border-primary-700"
                      >
                        <Icon className="h-5 w-5 shrink-0 text-primary-500" />
                        <span className="text-sm text-gray-700 group-hover:text-gray-900 dark:text-gray-300 dark:group-hover:text-white">
                          {prompt.text}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* Message List */
          <div className="space-y-1 py-2">
            {messages.map((message, index) => (
              <ChatMessage
                key={message.id}
                message={message}
                isLast={index === messages.length - 1}
              />
            ))}

            {/* Streaming structured triage */}
            {isStreaming && isTriageReportStream && streamingTriage && (
              <div className="bg-white/60 dark:bg-gray-900/40">
                <div className={`${messageRowClass} py-5`}>
                  <div className="shrink-0">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 dark:bg-primary-950">
                      <Sparkles className="h-4 w-4 text-primary-600 dark:text-primary-400" />
                    </div>
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="mb-1 flex items-center gap-2">
                      <span className="text-sm font-semibold text-gray-900 dark:text-white">
                        GuardianHealth
                      </span>
                    </div>
                    <StreamingTriageCard triage={streamingTriage} />
                  </div>
                </div>
              </div>
            )}

            {/* Streaming follow-up */}
            {isStreaming && isFollowUpStream && streamingTriage && (
              <div className="bg-white/60 dark:bg-gray-900/40">
                <div className={`${messageRowClass} py-5`}>
                  <div className="shrink-0">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 dark:bg-primary-950">
                      <Sparkles className="h-4 w-4 text-primary-600 dark:text-primary-400" />
                    </div>
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="mb-1 flex items-center gap-2">
                      <span className="text-sm font-semibold text-gray-900 dark:text-white">
                        GuardianHealth
                      </span>
                    </div>
                    <StreamingFollowUp triage={streamingTriage} />
                  </div>
                </div>
              </div>
            )}

            {/* Typing indicator — matches ChatMessage row layout */}
            {isTyping && (
              <div className="bg-white/60 dark:bg-gray-900/40">
                <div className={`${messageRowClass} py-5`}>
                  <div className="shrink-0">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 dark:bg-primary-950">
                      <Sparkles className="h-4 w-4 text-primary-600 dark:text-primary-400" />
                    </div>
                  </div>
                  <div className="min-w-0 flex-1 pt-1">
                    {statusMessage && (
                      <p className="mb-2 text-sm text-gray-500 dark:text-gray-400">
                        {statusMessage}
                      </p>
                    )}
                    <div className="flex items-center gap-1">
                      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.3s] dark:bg-gray-600" />
                      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.15s] dark:bg-gray-600" />
                      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 dark:bg-gray-600" />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Error message */}
            {error && (
              <div className={messageRowClass}>
                <div className="flex w-full items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-950/30">
                  <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-red-600 dark:text-red-400" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-red-900 dark:text-red-100">
                      Something went wrong
                    </p>
                    <p className="mt-0.5 text-sm text-red-700 dark:text-red-300">
                      {error}
                    </p>
                  </div>
                  <button
                    onClick={() => window.location.reload()}
                    className="rounded-lg p-1.5 text-red-600 transition-colors hover:bg-red-100 dark:text-red-400 dark:hover:bg-red-900/30"
                  >
                    <RefreshCw className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area — padding matches sidebar footer */}
      <div className="shrink-0 border-t border-gray-200/80 bg-white/90 px-4 py-4 backdrop-blur-sm dark:border-gray-800 dark:bg-gray-950/90 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl">
          <SymptomInput
            onSend={handleSend}
            isLoading={isLoading || isStreaming}
            placeholder="Describe your symptoms or ask a question..."
          />
        </div>
      </div>
    </div>
  );
}
