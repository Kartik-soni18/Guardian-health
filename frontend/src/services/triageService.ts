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
  assessment: string;
  reasoning: string;
  what_to_do: string[];
  what_not_to_do: string[];
  likely_conditions: string[];
  red_flags: string[];
  confidence: number;
  dataset_used: boolean;
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
  const assessment = data.assessment || data.response;
  return {
    id: data.audit_hash || crypto.randomUUID(),
    severity: mapSeverity(data.triage_level),
    summary: assessment,
    assessment,
    reasoning: data.reasoning,
    whatToDo: data.what_to_do || [],
    whatNotToDo: data.what_not_to_do || [],
    likelyConditions: data.likely_conditions || [],
    redFlags: data.red_flags || [],
    remedies: data.what_to_do || [],
    followUp: data.routing,
    symptoms: data.symptoms,
    confidence: data.confidence || (data.compliance_passed ? 0.7 : 0.4),
    datasetUsed: data.dataset_used,
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
