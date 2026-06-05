import { create } from 'zustand';
import { Chat, ChatMessage, PartialTriageResponse } from '@/types';

interface ChatState {
  chats: Chat[];
  currentChatId: string | null;
  messages: ChatMessage[];
  isLoading: boolean;
  isStreaming: boolean;
  streamingContent: string;
  streamingTriage: PartialTriageResponse | null;
  statusMessage: string;
  error: string | null;

  setChats: (chats: Chat[]) => void;
  addChat: (chat: Chat) => void;
  removeChat: (chatId: string) => void;
  setCurrentChat: (chatId: string | null) => void;
  setMessages: (messages: ChatMessage[]) => void;
  addMessage: (message: ChatMessage) => void;
  updateMessage: (messageId: string, updates: Partial<ChatMessage>) => void;
  appendStreamingContent: (chunk: string) => void;
  setStreamingContent: (content: string) => void;
  mergeStreamingTriage: (partial: PartialTriageResponse) => void;
  setStreamingTriage: (triage: PartialTriageResponse | null) => void;
  setStatusMessage: (message: string) => void;
  setIsLoading: (loading: boolean) => void;
  setIsStreaming: (streaming: boolean) => void;
  setError: (error: string | null) => void;
  clearStreaming: () => void;
}

export const useChatStore = create<ChatState>()((set, _get) => ({
  chats: [],
  currentChatId: null,
  messages: [],
  isLoading: false,
  isStreaming: false,
  streamingContent: '',
  streamingTriage: null,
  statusMessage: '',
  error: null,

  setChats: (chats) => set({ chats }),

  addChat: (chat) =>
    set((state) => ({
      chats: [{ ...chat, messages: chat.messages || [] }, ...state.chats],
      currentChatId: chat.id,
      messages: chat.messages || [],
    })),

  removeChat: (chatId) =>
    set((state) => {
      const newChats = state.chats.filter((c) => c.id !== chatId);
      return {
        chats: newChats,
        currentChatId:
          state.currentChatId === chatId
            ? newChats[0]?.id || null
            : state.currentChatId,
        messages:
          state.currentChatId === chatId
            ? []
            : state.messages,
      };
    }),

  setCurrentChat: (chatId) =>
    set({
      currentChatId: chatId,
      messages: [],
      error: null,
    }),

  setMessages: (messages) => set({ messages }),

  addMessage: (message) =>
    set((state) => {
      const messages = [...state.messages, message];
      const chats = state.chats.map((chat) =>
        chat.id === message.chatId
          ? { ...chat, messages, updatedAt: new Date().toISOString() }
          : chat
      );
      return { messages, chats };
    }),

  updateMessage: (messageId, updates) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === messageId ? { ...m, ...updates } : m
      ),
    })),

  appendStreamingContent: (chunk) =>
    set((state) => ({
      streamingContent: state.streamingContent + chunk,
    })),

  setStreamingContent: (content) => set({ streamingContent: content }),

  mergeStreamingTriage: (partial) =>
    set((state) => ({
      streamingTriage: {
        ...(state.streamingTriage || {}),
        ...partial,
        immediateActions: partial.immediateActions ?? state.streamingTriage?.immediateActions,
        crucialWarnings: partial.crucialWarnings ?? state.streamingTriage?.crucialWarnings,
        resourceRecommendations:
          partial.resourceRecommendations ?? state.streamingTriage?.resourceRecommendations,
        requiredFollowUp: partial.requiredFollowUp ?? state.streamingTriage?.requiredFollowUp,
        likelyConditions: partial.likelyConditions ?? state.streamingTriage?.likelyConditions,
        followUpQuestions: partial.followUpQuestions ?? state.streamingTriage?.followUpQuestions,
        assumptions: partial.assumptions ?? state.streamingTriage?.assumptions,
      },
    })),

  setStreamingTriage: (triage) => set({ streamingTriage: triage }),

  setStatusMessage: (message) => set({ statusMessage: message }),

  setIsLoading: (loading) => set({ isLoading: loading }),

  setIsStreaming: (streaming) => set({ isStreaming: streaming }),

  setError: (error) => set({ error }),

  clearStreaming: () =>
    set({
      isStreaming: false,
      streamingContent: '',
      streamingTriage: null,
      statusMessage: '',
    }),
}));
