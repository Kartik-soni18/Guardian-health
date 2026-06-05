import { api } from './api';
import { ChatMessage, TriageRequest, TriageResponse } from '@/types';

interface BackendTriageRequest {
  query: string;
  chat_id?: string;
  conversation_history?: Array<{ role: string; content: string }>;
}

interface BackendTriageResponse {
  response: string;
  triage_level?: string | null;
  routing: string;
  symptoms: string[];
  reasoning: string;
  compliance_passed: boolean;
  audit_hash?: string | null;
  disclaimer: string;
}

function mapSeverity(level?: string | null): TriageResponse['severity'] {
  switch (level) {
    case 'emergent':
      return 'emergency';
    case 'urgent':
      return 'urgent';
    case 'self_care':
      return 'self-care';
    case 'routine':
      return 'urgent';
    default:
      return 'unknown';
  }
}

function mapTriageResponse(data: BackendTriageResponse): TriageResponse {
  return {
    id: data.audit_hash || crypto.randomUUID(),
    severity: mapSeverity(data.triage_level),
    summary: data.response,
    reasoning: data.reasoning,
    redFlags: [],
    remedies: [],
    followUp: data.routing,
    symptoms: data.symptoms,
    confidence: data.compliance_passed ? 0.8 : 0.5,
    createdAt: new Date().toISOString(),
    disclaimer: data.disclaimer,
  };
}

export const triageService = {
  async submitTriage(
    request: TriageRequest,
    options?: {
      chatId?: string;
      history?: ChatMessage[];
    }
  ): Promise<TriageResponse> {
    const payload: BackendTriageRequest = {
      query: request.query || request.symptoms,
      chat_id: options?.chatId,
      conversation_history: options?.history?.map((msg) => ({
        role: msg.role,
        content: msg.content,
      })),
    };

    const response = await api.post<BackendTriageResponse>('/triage', payload);
    return mapTriageResponse(response.data);
  },
};
