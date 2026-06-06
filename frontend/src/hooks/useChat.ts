import { useCallback, useEffect, useState } from 'react';
import { chatService } from '@/services/chatService';
import { triageService } from '@/services/triageService';
import { useChatStore } from '@/stores/chatStore';
import { useAuthStore } from '@/stores/authStore';
import { Chat, ChatMessage, TriageRequest } from '@/types';

export function useChat() {
  const userId = useAuthStore((s) => s.user?.id);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const {
    chats,
    currentChatId,
    messages,
    isLoading,
    isStreaming,
    streamingContent,
    streamingTriage,
    error,
    addChat,
    removeChat,
    setChats,
    setCurrentChat,
    setMessages,
    addMessage,
    statusMessage,
    setIsLoading,
    setIsStreaming,
    setStreamingContent,
    setStreamingTriage,
    setStatusMessage,
    mergeStreamingTriage,
    setError,
    clearStreaming,
  } = useChatStore();

  const [isDeletingChat, setIsDeletingChat] = useState(false);

  const refreshChats = useCallback(async () => {
    if (!isAuthenticated) {
      setChats([]);
      return;
    }
    setIsLoading(true);
    try {
      const loaded = await chatService.listChats();
      setChats(loaded);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load chats');
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, setChats, setError, setIsLoading]);

  useEffect(() => {
    if (isAuthenticated) {
      void refreshChats();
    } else {
      setChats([]);
      setCurrentChat(null);
      setMessages([]);
    }
  }, [isAuthenticated, refreshChats, setChats, setCurrentChat, setMessages]);

  const loadChat = useCallback(
    async (chatId: string) => {
      setCurrentChat(chatId);
      setIsLoading(true);
      setError(null);
      try {
        const chat = await chatService.getChat(chatId);
        setMessages(chat.messages);
        setChats(
          useChatStore.getState().chats.map((item) =>
            item.id === chatId
              ? { ...item, title: chat.title, updatedAt: chat.updatedAt, messages: chat.messages }
              : item
          )
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load chat');
        setMessages([]);
      } finally {
        setIsLoading(false);
      }
    },
    [setChats, setCurrentChat, setError, setIsLoading, setMessages]
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
      setStreamingTriage(null);
      setStatusMessage('');
      setError(null);

      const request = { query: content, symptoms: content } as TriageRequest;
      const options = { chatId };

      const addAssistantMessage = (
        triage: Awaited<ReturnType<typeof triageService.submitTriage>>
      ) => {
        const assistantMessage: ChatMessage = {
          id: crypto.randomUUID(),
          chatId,
          role: 'assistant',
          content: triage.summary || triage.assessment,
          triage: triage.needsFollowUp ? null : triage,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        addMessage(assistantMessage);
      };

      try {
        let triage = await triageService.streamTriage(
          request,
          {
            onStatus: setStatusMessage,
            onPartial: mergeStreamingTriage,
          },
          options
        );

        if (!triage) {
          triage = await triageService.submitTriage(request, options);
        }

        addAssistantMessage(triage);
        await refreshChats();
      } catch (err) {
        try {
          const triage = await triageService.submitTriage(request, options);
          addAssistantMessage(triage);
          await refreshChats();
        } catch (fallbackErr) {
          setError(
            fallbackErr instanceof Error
              ? fallbackErr.message
              : err instanceof Error
                ? err.message
                : 'Failed to send message'
          );
        }
      } finally {
        clearStreaming();
      }
    },
    [
      addMessage,
      clearStreaming,
      mergeStreamingTriage,
      refreshChats,
      setError,
      setIsStreaming,
      setStatusMessage,
      setStreamingContent,
      setStreamingTriage,
    ]
  );

  const createNewChat = useCallback(
    async (initialMessage?: string): Promise<Chat | null> => {
      try {
        const chat = await chatService.createChat(initialMessage);
        addChat({ ...chat, userId: userId || chat.userId, messages: [] });
        return chat;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to create chat');
        return null;
      }
    },
    [addChat, setError, userId]
  );

  const deleteChat = useCallback(
    async (chatId: string) => {
      setIsDeletingChat(true);
      try {
        await chatService.deleteChat(chatId);
        removeChat(chatId);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete chat');
        throw err;
      } finally {
        setIsDeletingChat(false);
      }
    },
    [removeChat, setError]
  );

  return {
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
    refreshChats,
  };
};
