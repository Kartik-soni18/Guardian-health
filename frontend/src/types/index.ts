export interface User {
  id: string;
  username: string;
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
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  password: string;
}

export interface TriageRequest {
  query: string;
  symptoms: string;
  chatId?: string;
  conversationHistory?: Array<{ role: string; content: string }>;
}

export type TriageLevel =
  | 'level_1'
  | 'level_2'
  | 'level_3'
  | 'level_4'
  | 'level_5'
  | 'unknown';

export interface PartialTriageResponse {
  responseMode?: 'follow_up' | 'triage_report';
  triageLevel?: TriageLevel;
  levelTitle?: string;
  levelJustification?: string;
  assessment?: string;
  preliminaryAssessment?: string;
  immediateActions?: string[];
  crucialWarnings?: string[];
  resourceRecommendations?: string[];
  requiredFollowUp?: string[];
  likelyConditions?: string[];
  followUpQuestions?: string[];
  assumptions?: string[];
}

export interface TriageResponse {
  id: string;
  triageLevel: TriageLevel;
  levelTitle: string;
  levelJustification: string;
  severity: 'emergency' | 'urgent' | 'self-care' | 'unknown';
  responseMode: 'follow_up' | 'triage_report';
  needsFollowUp: boolean;
  followUpQuestions: string[];
  summary: string;
  assessment: string;
  reasoning: string;
  immediateActions: string[];
  crucialWarnings: string[];
  resourceRecommendations: string[];
  requiredFollowUp: string[];
  assumptions: string[];
  whatToDo: string[];
  whatNotToDo: string[];
  likelyConditions: string[];
  redFlags: string[];
  remedies: string[];
  followUp: string;
  symptoms: string[];
  careSetting?: string;
  confidence: number;
  datasetUsed: boolean;
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
