import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { api } from '@/utils/api';
interface User {
  username: string;
  token: string;
}

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const token = localStorage.getItem('guardian_token');
    const username = localStorage.getItem('guardian_user');
    if (token && username) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      return { username, token };
    }
    return null;
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user?.token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${user.token}`;
    } else {
      delete api.defaults.headers.common['Authorization'];
    }
  }, [user]);

  const login = useCallback(async (username: string, password: string) => {
    setLoading(true);
    try {
      const response = await api.post('/login', { username, password });
      const { access_token } = response.data;
      localStorage.setItem('guardian_token', access_token);
      localStorage.setItem('guardian_user', username);
      setUser({ username, token: access_token });
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(async (username: string, password: string) => {
    setLoading(true);
    try {
      const response = await api.post('/register', { username, password });
      const { access_token } = response.data;
      localStorage.setItem('guardian_token', access_token);
      localStorage.setItem('guardian_user', username);
      setUser({ username, token: access_token });
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('guardian_token');
    localStorage.removeItem('guardian_user');
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
