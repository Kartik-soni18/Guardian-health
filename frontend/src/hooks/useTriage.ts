import { useState, useCallback } from 'react';
import { api } from '@/utils/api';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  type?: 'triage' | 'diagnosis' | 'emergency' | 'follow_up' | 'rejected';
  privacy?: { pii_detected: boolean };
  metadata?: Record<string, unknown>;
  timestamp: Date;
}

export interface Chat {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export function useTriage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);

  const sendMessage = useCallback(async (
    query: string,
    conversationHistory: Message[] = []
  ) => {
    if (!query.trim()) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      const history = conversationHistory.map(m => ({
        role: m.role,
        content: m.content,
      }));

      const response = await api.post('/triage', {
        query,
        chat_id: currentChatId,
        conversation_history: history,
      });

      const data = response.data;

      const botMessage: Message = {
        id: `bot-${Date.now()}`,
        role: 'assistant',
        content: data.response || data.message || JSON.stringify(data),
        type: data.status || 'triage',
        privacy: data.privacy,
        metadata: {
          triage_level: data.triage_level,
          disease: data.disease,
          disease_name: data.disease_name,
          confidence: data.confidence,
          symptoms: data.symptoms,
          red_flags: data.red_flags,
          remedies: data.remedies,
          care_advice: data.care_advice,
          otc_products: data.otc_products,
          all_predictions: data.all_predictions,
          research: data.research,
          reasoning: data.reasoning,
          audit: data.audit,
          ...data,
        },
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, botMessage]);

      if (data.chat_id && !currentChatId) {
        setCurrentChatId(data.chat_id);
      }

      return botMessage;
    } catch (error) {
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'I apologize, but I encountered an error processing your request. Please try again.',
        type: 'triage',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
      return errorMessage;
    } finally {
      setLoading(false);
    }
  }, [currentChatId]);

  const loadChat = useCallback(async (chatId: string) => {
    try {
      const response = await api.get(`/chats/${chatId}`);
      // Backend returns messages array directly, not wrapped in a chat object
      const rawMessages = Array.isArray(response.data) ? response.data : response.data.messages || [];
      const normalized = rawMessages.map((m: any) => {
        const base = {
          id: m.id || `${m.role}-${Date.now()}-${Math.random()}`,
          role: m.role,
          timestamp: new Date(m.timestamp || m.created_at),
        };
        // Assistant messages stored in MongoDB have content = full response object
        if (m.role === 'assistant' && typeof m.content === 'object' && m.content !== null) {
          const data = m.content;
          return {
            ...base,
            content: data.response || data.message || JSON.stringify(data),
            type: data.status || 'triage',
            privacy: data.privacy,
            metadata: {
              triage_level: data.triage_level,
              disease: data.disease,
              disease_name: data.disease_name,
              confidence: data.confidence,
              symptoms: data.symptoms,
              red_flags: data.red_flags,
              remedies: data.remedies,
              care_advice: data.care_advice,
              otc_products: data.otc_products,
              all_predictions: data.all_predictions,
              research: data.research,
              reasoning: data.reasoning,
              audit: data.audit,
              ...data,
            },
          };
        }
        return {
          ...base,
          content: typeof m.content === 'string' ? m.content : JSON.stringify(m.content),
          type: m.type || 'triage',
          privacy: m.privacy,
          metadata: m.metadata,
        };
      });
      setMessages(normalized);
      setCurrentChatId(chatId);
    } catch (error) {
      console.error('Failed to load chat:', error);
    }
  }, []);

  const newChat = useCallback(() => {
    setMessages([]);
    setCurrentChatId(null);
  }, []);

  const deleteChat = useCallback(async (chatId: string) => {
    try {
      await api.delete(`/chats/${chatId}`);
      if (currentChatId === chatId) {
        newChat();
      }
    } catch (error) {
      console.error('Failed to delete chat:', error);
    }
  }, [currentChatId, newChat]);

  return {
    messages,
    loading,
    currentChatId,
    sendMessage,
    loadChat,
    newChat,
    deleteChat,
    setMessages,
  };
}

export default useTriage;
