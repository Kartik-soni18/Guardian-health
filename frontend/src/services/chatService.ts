import { api } from './api';
import { useAuthStore } from '@/stores/authStore';
import { Chat, ChatMessage } from '@/types';

export const chatService = {
  async listChats(): Promise<Chat[]> {
    const response = await api.get('/chats');
    return response.data;
  },

  async createChat(initialMessage?: string): Promise<Chat> {
    const response = await api.post('/chats', { initialMessage });
    return response.data;
  },

  async getChat(id: string): Promise<Chat & { messages: ChatMessage[] }> {
    const response = await api.get(`/chats/${id}`);
    return response.data;
  },

  async deleteChat(id: string): Promise<void> {
    await api.delete(`/chats/${id}`);
  },

  async sendMessage(chatId: string, content: string): Promise<ChatMessage> {
    const response = await api.post(`/chats/${chatId}/messages`, { content });
    return response.data;
  },

  async streamMessage(
    chatId: string,
    content: string,
    onChunk: (chunk: string) => void,
    onComplete: (message: ChatMessage) => void,
    onError: (error: Error) => void
  ): Promise<void> {
    try {
      const token = useAuthStore.getState().accessToken;
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || '/api'}/chats/${chatId}/messages/stream`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ content }),
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No reader available');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              onComplete({
                id: crypto.randomUUID(),
                chatId,
                role: 'assistant',
                content: buffer,
                triage: null,
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString(),
              });
              return;
            }
            try {
              const parsed = JSON.parse(data);
              if (parsed.chunk) {
                onChunk(parsed.chunk);
              }
              if (parsed.message) {
                onComplete(parsed.message);
                return;
              }
            } catch {
              onChunk(data);
            }
          }
        }
      }
    } catch (error) {
      onError(error instanceof Error ? error : new Error('Stream failed'));
    }
  },
};
