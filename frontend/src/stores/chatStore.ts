import { create } from 'zustand';
import { Chat, ChatMessage } from '@/types';

interface ChatState {
  chats: Chat[];
  currentChatId: string | null;
  messages: ChatMessage[];
  isLoading: boolean;
  isStreaming: boolean;
  streamingContent: string;
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
  setIsLoading: (loading: boolean) => void;
  setIsStreaming: (streaming: boolean) => void;
  setError: (error: string | null) => void;
  clearStreaming: () => void;
}

export const useChatStore = create<ChatState>()((set, get) => ({
  chats: [],
  currentChatId: null,
  messages: [],
  isLoading: false,
  isStreaming: false,
  streamingContent: '',
  error: null,

  setChats: (chats) => set({ chats }),

  addChat: (chat) =>
    set((state) => ({
      chats: [chat, ...state.chats],
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
    set((state) => ({
      messages: [...state.messages, message],
    })),

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

  setIsLoading: (loading) => set({ isLoading: loading }),

  setIsStreaming: (streaming) => set({ isStreaming: streaming }),

  setError: (error) => set({ error }),

  clearStreaming: () =>
    set({
      isStreaming: false,
      streamingContent: '',
    }),
}));
