export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  createdAt: string;
  updatedAt: string;
}

export interface TokenResponse {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
}

export interface TriageRequest {
  symptoms: string;
  age?: number;
  gender?: 'male' | 'female' | 'other';
  duration?: string;
  severity?: 'mild' | 'moderate' | 'severe';
  medicalHistory?: string[];
  medications?: string[];
  allergies?: string[];
}

export interface TriageResponse {
  id: string;
  severity: 'emergency' | 'urgent' | 'self-care' | 'unknown';
  summary: string;
  reasoning: string;
  redFlags: string[];
  remedies: string[];
  followUp: string;
  symptoms: string[];
  confidence: number;
  createdAt: string;
  disclaimer: string;
}

export interface Chat {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  userId: string;
  messages?: ChatMessage[];
}

export interface ChatMessage {
  id: string;
  chatId: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  triage?: TriageResponse | null;
  createdAt: string;
  updatedAt: string;
}

export interface ApiError {
  message: string;
  code: string;
  status: number;
  details?: Record<string, string[]>;
}

export type ThemeMode = 'light' | 'dark' | 'system';

export interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
}
