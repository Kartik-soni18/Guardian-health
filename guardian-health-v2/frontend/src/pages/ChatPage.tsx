import { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { useChat } from '@/hooks/useChat';
import { useToast } from '@/hooks/useToast';
import { ChatSidebar } from '@/components/ChatSidebar';
import { ChatInterface } from '@/components/ChatInterface';
import { AuthModal } from '@/components/AuthModal';

export function ChatPage() {
  const location = useLocation();
  const navigate = useNavigate();
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
  const initialQueryHandled = useRef(false);

  // Handle initialQuery from navigation state
  useEffect(() => {
    const state = location.state as { initialQuery?: string } | null;
    if (state?.initialQuery && !initialQueryHandled.current) {
      initialQueryHandled.current = true;
      handleStartChat(state.initialQuery);
      // Clear the state so refreshing doesn't re-trigger
      navigate(location.pathname, { replace: true, state: {} });
    }
  }, [location.state, location.pathname]);

  // Clear initial query ref when chat changes
  useEffect(() => {
    if (!currentChatId) {
      initialQueryHandled.current = false;
    }
  }, [currentChatId]);

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
        // Create new chat if none selected
        await handleStartChat(content);
        return;
      }
      await sendMessage(currentChatId, content);
    },
    [currentChatId, sendMessage, handleStartChat]
  );

  const handleSelectChat = useCallback(
    async (chatId: string) => {
      if (chatId === currentChatId) return;
      await loadChat(chatId);
    },
    [currentChatId, loadChat]
  );

  const handleNewChat = useCallback(async () => {
    setCurrentChat(null);
  }, [setCurrentChat]);

  const handleDeleteChat = useCallback(
    async (chatId: string) => {
      try {
        await deleteChat(chatId);
        toast.success('Chat deleted');
      } catch {
        toast.error('Failed to delete chat');
      }
    },
    [deleteChat, toast]
  );

  return (
    <div className="flex h-[calc(100vh-4rem-4rem)] overflow-hidden bg-gray-50 dark:bg-gray-950">
      {/* Sidebar */}
      <ChatSidebar
        chats={chats}
        currentChatId={currentChatId}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
        isLoading={isLoading}
        isDeleting={isDeletingChat}
      />

      {/* Chat Interface */}
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

      {/* Auth Modal */}
      <AuthModal
        isOpen={showAuth}
        onClose={() => setShowAuth(false)}
        defaultTab="login"
      />
    </div>
  );
}
