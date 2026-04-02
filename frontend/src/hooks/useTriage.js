import { useState, useCallback } from 'react';
import api from '../utils/api';

export const useTriage = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getTriage = async (query, chatId, conversationHistory = null) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/triage', {
        query,
        chat_id: chatId,
        conversation_history: conversationHistory,
      });
      return response.data;
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong');
      return null;
    } finally {
      setLoading(false);
    }
  };

  const getChats = useCallback(async () => {
    try {
      const response = await api.get('/chats');
      return response.data;
    } catch (err) {
      console.error('Failed to load chats', err);
      return [];
    }
  }, []);

  const getChatHistory = useCallback(async (chatId) => {
    try {
      const response = await api.get(`/chats/${chatId}`);
      return response.data;
    } catch (err) {
      console.error('Failed to load chat history', err);
      return [];
    }
  }, []);

  const deleteChat = useCallback(async (chatId) => {
    try {
      await api.delete(`/chats/${chatId}`);
      return true;
    } catch (err) {
      console.error('Failed to delete chat', err);
      return false;
    }
  }, []);

  // For compatibility during HMR reloads
  const getHistory = getChatHistory;

  return { getTriage, getChats, getChatHistory, getHistory, deleteChat, loading, error };
};
