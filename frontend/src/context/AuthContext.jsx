import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../utils/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      // In a real app, we might verify the token here
      const savedUser = localStorage.getItem('username');
      if (savedUser) setUser({ username: savedUser });
    }
    setLoading(false);
  }, [token]);

  const login = async (username, password) => {
    try {
      const response = await api.post('/login', { username, password });
      const { access_token, username: resUser } = response.data;
      setToken(access_token);
      setUser({ username: resUser });
      localStorage.setItem('token', access_token);
      localStorage.setItem('username', resUser);
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      return { success: true };
    } catch (err) {
      return { success: false, error: err.response?.data?.detail || 'Login failed' };
    }
  };

  const register = async (username, password) => {
    try {
      const response = await api.post('/register', { username, password });
      const { access_token, username: resUser } = response.data;
      setToken(access_token);
      setUser({ username: resUser });
      localStorage.setItem('token', access_token);
      localStorage.setItem('username', resUser);
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      return { success: true };
    } catch (err) {
      return { success: false, error: err.response?.data?.detail || 'Registration failed' };
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    delete api.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, register, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
