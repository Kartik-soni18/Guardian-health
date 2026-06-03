import { api } from './api';
import { LoginCredentials, RegisterData, TokenResponse, User } from '@/types';

export const authService = {
  async login(credentials: LoginCredentials): Promise<TokenResponse & { user: User }> {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },

  async register(data: RegisterData): Promise<TokenResponse & { user: User }> {
    const response = await api.post('/auth/register', data);
    return response.data;
  },

  async refreshToken(token: string): Promise<TokenResponse> {
    const response = await api.post('/auth/refresh', { refreshToken: token });
    return response.data;
  },

  async getMe(): Promise<User> {
    const response = await api.get('/auth/me');
    return response.data;
  },

  async logout(): Promise<void> {
    const refreshToken = localStorage.getItem('refreshToken');
    if (refreshToken) {
      try {
        await api.post('/auth/logout', { refreshToken });
      } catch {
        // Ignore logout errors
      }
    }
  },
};
