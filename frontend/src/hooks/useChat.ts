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
    streamingTriage,
    error,
    addChat,
    removeChat,
    setCurrentChat,
    setMessages,
    addMessage,
    statusMessage,
    setIsStreaming,
    setStreamingContent,
    setStreamingTriage,
    setStatusMessage,
    mergeStreamingTriage,
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
      setStreamingTriage(null);
      setStatusMessage('');

      const history = [...messages, userMessage];
      const request = { query: content, symptoms: content } as TriageRequest;
      const options = { chatId, history };

      const addAssistantMessage = (triage: Awaited<ReturnType<typeof triageService.submitTriage>>) => {
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
      } catch (err) {
        try {
          const triage = await triageService.submitTriage(request, options);
          addAssistantMessage(triage);
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
      messages,
      setError,
      setIsStreaming,
      setStatusMessage,
      setStreamingContent,
      setStreamingTriage,
    ]
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
    streamingTriage,
    statusMessage,
    error,
    loadChat,
    sendMessage,
    createNewChat,
    deleteChat,
    isDeletingChat: false,
    setCurrentChat,
  };
}
