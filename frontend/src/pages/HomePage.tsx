import { useState, useCallback } from 'react';
import { AlertTriangle } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useChat } from '@/hooks/useChat';
import { useToast } from '@/hooks/useToast';
import { ChatSidebar } from '@/components/ChatSidebar';
import { ChatInterface } from '@/components/ChatInterface';
import { AuthModal } from '@/components/AuthModal';

export function HomePage() {
  const { isAuthenticated } = useAuth();
  const toast = useToast();
  const {
    chats,
    currentChatId,
    messages,
    isLoading,
    isStreaming,
    streamingContent,
    error,
    loadChat,
    sendMessage,
    createNewChat,
    deleteChat,
    isDeletingChat,
    setCurrentChat,
  } = useChat();

  const [showAuth, setShowAuth] = useState(false);

  const handleStartChat = useCallback(
    async (content: string) => {
      if (!isAuthenticated) {
        setShowAuth(true);
        return;
      }
      try {
        const chat = await createNewChat(content);
        if (chat) {
          await sendMessage(chat.id, content);
        }
      } catch {
        toast.error('Failed to start chat. Please try again.');
      }
    },
    [isAuthenticated, createNewChat, sendMessage, toast]
  );

  const handleSendMessage = useCallback(
    async (content: string) => {
      if (!currentChatId) {
        await handleStartChat(content);
        return;
      }
      await sendMessage(currentChatId, content);
    },
    [currentChatId, sendMessage, handleStartChat]
  );

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col overflow-hidden bg-gray-50 dark:bg-gray-950">
      <div className="flex flex-1 overflow-hidden">
        <ChatSidebar
          chats={chats}
          currentChatId={currentChatId}
          onSelectChat={(id) => loadChat(id)}
          onNewChat={() => setCurrentChat(null)}
          onDeleteChat={deleteChat}
          isLoading={isLoading}
          isDeleting={isDeletingChat}
        />
        <div className="flex flex-1 flex-col overflow-hidden">
          <ChatInterface
            messages={messages}
            isLoading={isLoading}
            isStreaming={isStreaming}
            streamingContent={streamingContent}
            error={error}
            onSendMessage={handleSendMessage}
            onStartChat={handleStartChat}
            chatId={currentChatId}
          />
        </div>
      </div>

      <div className="shrink-0 border-t border-gray-200 bg-white px-4 py-3 dark:border-gray-800 dark:bg-gray-900">
        <div className="mx-auto flex max-w-3xl items-start gap-2 text-xs leading-relaxed text-gray-500 dark:text-gray-400">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" />
          <p>
            GuardianHealth is an AI triage tool for general health information only. It is not a
            substitute for professional medical advice, diagnosis, or treatment. For emergencies,
            call 911 or your local emergency services.
          </p>
        </div>
      </div>

      <AuthModal isOpen={showAuth} onClose={() => setShowAuth(false)} defaultTab="login" />
    </div>
  );
}
