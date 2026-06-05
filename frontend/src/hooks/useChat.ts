import { useCallback } from 'react';
import { triageService } from '@/services/triageService';
import { useChatStore } from '@/stores/chatStore';
import { useAuthStore } from '@/stores/authStore';
import { Chat, ChatMessage, TriageRequest } from '@/types';

function buildChatTitle(content: string): string {
  const trimmed = content.trim();
  return trimmed.length > 48 ? `${trimmed.slice(0, 48)}…` : trimmed || 'New chat';
}

export function useChat() {
  const userId = useAuthStore((s) => s.user?.id);
  const {
    chats,
    currentChatId,
    messages,
    isLoading,
    isStreaming,
    streamingContent,
    error,
    addChat,
    removeChat,
    setCurrentChat,
    setMessages,
    addMessage,
    setIsStreaming,
    setStreamingContent,
    setError,
    clearStreaming,
  } = useChatStore();

  const loadChat = useCallback(
    async (chatId: string) => {
      const chat = chats.find((item) => item.id === chatId);
      setCurrentChat(chatId);
      setMessages(chat?.messages || []);
    },
    [chats, setCurrentChat, setMessages]
  );

  const sendMessage = useCallback(
    async (chatId: string, content: string) => {
      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        chatId,
        role: 'user',
        content,
        triage: null,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      addMessage(userMessage);
      setIsStreaming(true);
      setStreamingContent('');

      const history = [...messages, userMessage];

      try {
        const triage = await triageService.submitTriage(
          { query: content, symptoms: content } as TriageRequest,
          { chatId, history }
        );

        const assistantMessage: ChatMessage = {
          id: crypto.randomUUID(),
          chatId,
          role: 'assistant',
          content: triage.assessment || triage.summary,
          triage,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        addMessage(assistantMessage);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to send message');
      } finally {
        clearStreaming();
      }
    },
    [addMessage, clearStreaming, messages, setError, setIsStreaming, setStreamingContent]
  );

  const createNewChat = useCallback(
    async (initialMessage?: string): Promise<Chat | null> => {
      const chat: Chat = {
        id: crypto.randomUUID(),
        title: buildChatTitle(initialMessage || 'New chat'),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        userId: userId || 'anonymous',
        messages: [],
      };
      addChat(chat);
      return chat;
    },
    [addChat, userId]
  );

  const deleteChat = useCallback(
    (chatId: string) => {
      removeChat(chatId);
    },
    [removeChat]
  );

  return {
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
    isDeletingChat: false,
    setCurrentChat,
  };
}
