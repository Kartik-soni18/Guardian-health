import { useState, useCallback } from 'react';
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
    streamingTriage,
    statusMessage,
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
    <div className="flex h-full min-h-0 flex-1 flex-col overflow-hidden bg-gray-50 dark:bg-gray-950">
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
            streamingTriage={streamingTriage}
            statusMessage={statusMessage}
            error={error}
            onSendMessage={handleSendMessage}
            onStartChat={handleStartChat}
            chatId={currentChatId}
          />
        </div>
      </div>

      <AuthModal isOpen={showAuth} onClose={() => setShowAuth(false)} defaultTab="login" />
    </div>
  );
}
