import { useRef, useEffect, useCallback } from 'react';
import {
  AlertTriangle,
  RefreshCw,
  MessageSquarePlus,
  Sparkles,
  Flame,
  Thermometer,
  Brain,
  Bone,
} from 'lucide-react';
import { ChatMessage as ChatMessageType } from '@/types';
import { ChatMessage } from './ChatMessage';
import { SymptomInput } from './SymptomInput';

interface ChatInterfaceProps {
  messages: ChatMessageType[];
  isLoading: boolean;
  isStreaming: boolean;
  streamingContent: string;
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

export function ChatInterface({
  messages,
  isLoading,
  isStreaming,
  streamingContent,
  error,
  onSendMessage,
  onStartChat,
}: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const hasMessages = messages.length > 0;
  const isTyping = isStreaming && streamingContent.length === 0;

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent, scrollToBottom]);

  const handleSend = (content: string) => {
    if (!hasMessages) {
      onStartChat(content);
    } else {
      onSendMessage(content);
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* Messages Area */}
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto scroll-smooth"
      >
        {!hasMessages && !isLoading ? (
          /* Empty State */
          <div className="flex h-full flex-col items-center justify-center px-4">
            <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary-100 dark:bg-primary-950">
              <Sparkles className="h-8 w-8 text-primary-600 dark:text-primary-400" />
            </div>
            <h2 className="mb-2 text-xl font-semibold text-gray-900 dark:text-white">
              How can I help you today?
            </h2>
            <p className="mb-8 max-w-md text-center text-sm text-gray-500 dark:text-gray-400">
              Describe your symptoms, ask health questions, or share concerns.
              I will help assess your condition and guide you to the right care.
            </p>

            {/* Suggested Prompts */}
            <div className="grid w-full max-w-lg gap-3 sm:grid-cols-2">
              {suggestedPrompts.map((prompt) => {
                const Icon = prompt.icon;
                return (
                  <button
                    key={prompt.text}
                    onClick={() => handleSend(prompt.text)}
                    className="group flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-4 text-left shadow-sm transition-all hover:border-primary-300 hover:shadow-md dark:border-gray-800 dark:bg-gray-900 dark:hover:border-primary-700"
                  >
                    <Icon className="h-5 w-5 shrink-0 text-primary-500" />
                    <span className="text-sm text-gray-700 group-hover:text-gray-900 dark:text-gray-300 dark:group-hover:text-white">
                      {prompt.text}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Start New Chat Button */}
            <button
              onClick={() => handleSend('Hello, I need help with my health.')}
              className="mt-6 inline-flex items-center gap-2 rounded-lg border border-dashed border-gray-300 px-4 py-2 text-sm text-gray-500 transition-colors hover:border-primary-400 hover:text-primary-600 dark:border-gray-700 dark:text-gray-400 dark:hover:border-primary-600 dark:hover:text-primary-400"
            >
              <MessageSquarePlus className="h-4 w-4" />
              Start a new conversation
            </button>
          </div>
        ) : (
          /* Message List */
          <div className="space-y-1 px-4 py-6 sm:px-6 lg:px-8">
            {messages.map((message, index) => (
              <ChatMessage
                key={message.id}
                message={message}
                isLast={index === messages.length - 1}
              />
            ))}

            {/* Streaming message */}
            {isStreaming && streamingContent && (
              <ChatMessage
                message={{
                  id: 'streaming',
                  chatId: '',
                  role: 'assistant',
                  content: streamingContent,
                  triage: null,
                  createdAt: new Date().toISOString(),
                  updatedAt: new Date().toISOString(),
                }}
                isLast
                isStreaming
              />
            )}

            {/* Typing indicator */}
            {isTyping && (
              <div className="flex items-center gap-2 px-4 py-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 dark:bg-primary-950">
                  <Sparkles className="h-4 w-4 text-primary-600 dark:text-primary-400" />
                </div>
                <div className="flex gap-1">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.3s] dark:bg-gray-600" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.15s] dark:bg-gray-600" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 dark:bg-gray-600" />
                </div>
              </div>
            )}

            {/* Error message */}
            {error && (
              <div className="mx-auto max-w-2xl">
                <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-950/30">
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

      {/* Input Area */}
      <div className="border-t border-gray-200 bg-white px-4 py-4 dark:border-gray-800 dark:bg-gray-950">
        <div className="mx-auto max-w-3xl">
          <SymptomInput
            onSend={handleSend}
            isLoading={isLoading || isStreaming}
            placeholder="Describe your symptoms or ask a question..."
          />
          <p className="mt-2 text-center text-xs text-gray-400 dark:text-gray-600">
            GuardianHealth provides general health information, not medical advice.
            In an emergency, call 911.
          </p>
        </div>
      </div>
    </div>
  );
}
