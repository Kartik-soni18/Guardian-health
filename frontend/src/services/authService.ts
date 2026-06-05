import { api } from './api';
import { LoginCredentials, RegisterData, TokenResponse, User } from '@/types';

interface BackendTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: string;
    username: string;
    email: string;
    full_name: string;
    role: string;
    is_active: boolean;
    is_verified: boolean;
    created_at: string;
  };
}

function mapUser(user: BackendTokenResponse['user']): User {
  const [firstName = '', ...rest] = user.full_name.split(' ');
  return {
    id: user.id,
    email: user.email,
    username: user.username,
    firstName,
    lastName: rest.join(' '),
    createdAt: user.created_at,
    updatedAt: user.created_at,
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

function deriveUsername(email: string, firstName: string): string {
  const local = email.split('@')[0].replace(/[^a-zA-Z0-9_]/g, '_').slice(0, 20);
  const name = firstName.replace(/[^a-zA-Z0-9_]/g, '_').slice(0, 10);
  const base = name || local || 'user';
  return `${base}_${Date.now().toString(36).slice(-4)}`;
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<TokenResponse & { user: User }> {
    const response = await api.post<BackendTokenResponse>('/auth/login', {
      username: credentials.username || credentials.email,
      password: credentials.password,
    });
    return mapTokenResponse(response.data);
  },

  async register(data: RegisterData): Promise<TokenResponse & { user: User }> {
    const response = await api.post<BackendTokenResponse>('/auth/register', {
      username: data.username || deriveUsername(data.email, data.firstName),
      email: data.email,
      password: data.password,
      full_name: `${data.firstName} ${data.lastName}`.trim(),
    });
    return mapTokenResponse(response.data);
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
    return;
  },
};
