import { api } from './api';
import { parseApiError } from '@/lib/utils';
import { LoginCredentials, RegisterData, TokenResponse, User } from '@/types';
function wrapAuthError(error: unknown, fallback: string): Error {
  return new Error(parseApiError(error, fallback));
}

interface BackendTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: string;
    username: string;
    role: string;
    is_active: boolean;
    is_verified: boolean;
    created_at: string;
    updated_at?: string;
  };
}

function mapUser(user: BackendTokenResponse['user']): User {
  return {
    id: user.id,
    username: user.username,
    createdAt: user.created_at,
    updatedAt: user.updated_at ?? user.created_at,
  };
}

function mapTokenResponse(data: BackendTokenResponse): TokenResponse & { user: User } {
  return {
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
    tokenType: data.token_type,
    expiresIn: data.expires_in,
    user: mapUser(data.user),
  };
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<TokenResponse & { user: User }> {
    try {
      const response = await api.post<BackendTokenResponse>('/auth/login', {
        username: credentials.username,
        password: credentials.password,
      });
      return mapTokenResponse(response.data);
    } catch (error) {
      throw wrapAuthError(error, 'Login failed');
    }
  },

  async loginWithGoogle(idToken: string): Promise<TokenResponse & { user: User }> {
    try {
      const response = await api.post<BackendTokenResponse>('/auth/google', {
        id_token: idToken,
      });
      return mapTokenResponse(response.data);
    } catch (error) {
      throw wrapAuthError(error, 'Google sign-in failed');
    }
  },

  async register(data: RegisterData): Promise<TokenResponse & { user: User }> {
    try {
      const response = await api.post<BackendTokenResponse>('/auth/register', {
        username: data.username,
        password: data.password,
      });
      return mapTokenResponse(response.data);
    } catch (error) {
      throw wrapAuthError(error, 'Registration failed');
    }
  },

  async refreshToken(token: string): Promise<TokenResponse> {
    const response = await api.post<BackendTokenResponse>('/auth/refresh', {
      refresh_token: token,
    });
    return mapTokenResponse(response.data);
  },

  async getMe(): Promise<User> {
    const response = await api.get<BackendTokenResponse['user']>('/auth/me');
    return mapUser(response.data);
  },

  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } catch {
      // Clear local session even if the server call fails.
    }
  },
};
