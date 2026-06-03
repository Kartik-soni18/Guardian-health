import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';
import { chatService } from '@/services/chatService';
import { useChatStore } from '@/stores/chatStore';
import { useAuthStore } from '@/stores/authStore';
import { Chat, ChatMessage } from '@/types';

export function useChat() {
  const queryClient = useQueryClient();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const {
    chats,
    currentChatId,
    messages,
    isLoading: storeLoading,
    isStreaming,
    streamingContent,
    error,
    setChats,
    addChat,
    removeChat,
    setCurrentChat,
    setMessages,
    addMessage,
    appendStreamingContent,
    setStreamingContent,
    setIsLoading,
    setIsStreaming,
    setError,
    clearStreaming,
  } = useChatStore();

  const chatsQuery = useQuery({
    queryKey: ['chats'],
    queryFn: async () => {
      const data = await chatService.listChats();
      setChats(data);
      return data;
    },
    enabled: isAuthenticated,
    staleTime: 30 * 1000,
  });

  const createChatMutation = useMutation({
    mutationFn: async (initialMessage?: string) => {
      const chat = await chatService.createChat(initialMessage);
      return chat;
    },
    onSuccess: (chat) => {
      addChat(chat);
      queryClient.invalidateQueries({ queryKey: ['chats'] });
    },
  });

  const deleteChatMutation = useMutation({
    mutationFn: async (chatId: string) => {
      await chatService.deleteChat(chatId);
      return chatId;
    },
    onSuccess: (chatId) => {
      removeChat(chatId);
      queryClient.invalidateQueries({ queryKey: ['chats'] });
    },
  });

  const loadChat = useCallback(
    async (chatId: string) => {
      setCurrentChat(chatId);
      setIsLoading(true);
      try {
        const data = await chatService.getChat(chatId);
        setMessages(data.messages || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load chat');
      } finally {
        setIsLoading(false);
      }
    },
    [setCurrentChat, setMessages, setIsLoading, setError]
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

      try {
        await chatService.streamMessage(
          chatId,
          content,
          (chunk) => {
            appendStreamingContent(chunk);
          },
          (assistantMessage) => {
            addMessage(assistantMessage);
            clearStreaming();
          },
          (err) => {
            setError(err.message);
            clearStreaming();
          }
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to send message');
        clearStreaming();
      }
    },
    [addMessage, setIsStreaming, setStreamingContent, appendStreamingContent, clearStreaming, setError]
  );

  const createNewChat = useCallback(
    async (initialMessage?: string): Promise<Chat | null> => {
      try {
        const chat = await createChatMutation.mutateAsync(initialMessage);
        return chat;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to create chat');
        return null;
      }
    },
    [createChatMutation, setError]
  );

  return {
    chats,
    currentChatId,
    messages,
    isLoading: storeLoading || chatsQuery.isLoading || createChatMutation.isPending,
    isStreaming,
    streamingContent,
    error,
    loadChat,
    sendMessage,
    createNewChat,
    deleteChat: deleteChatMutation.mutate,
    isDeletingChat: deleteChatMutation.isPending,
    setCurrentChat,
  };
}
