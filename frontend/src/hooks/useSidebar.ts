import { useState, useEffect, useCallback } from 'react';
import { api } from '@/utils/api';
import { useAuth } from '@/context/AuthContext';

export interface ChatSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  symptom_tags?: string[];
}

export function useSidebar() {
  const { user } = useAuth();
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchChats = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    try {
      const response = await api.get('/chats');
      setChats(response.data || []);
    } catch (error) {
      console.error('Failed to fetch chats:', error);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchChats();
  }, [fetchChats]);

  return { chats, loading, fetchChats };
}

export default useSidebar;
