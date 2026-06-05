import { api } from './api';
import { useAuthStore } from '@/stores/authStore';
import {
  ChatMessage,
  PartialTriageResponse,
  TriageLevel,
  TriageRequest,
  TriageResponse,
} from '@/types';

interface BackendTriageRequest {
  query: string;
  chat_id?: string;
  conversation_history?: Array<{ role: string; content: string }>;
}

interface BackendTriageResponse {
  response: string;
  triage_level?: string | null;
  level_title?: string | null;
  level_justification?: string;
  response_mode?: string;
  needs_follow_up?: boolean;
  follow_up_questions?: string[];
  routing: string;
  symptoms: string[];
  assessment: string;
  reasoning: string;
  immediate_actions?: string[];
  crucial_warnings?: string[];
  resource_recommendations?: string[];
  required_follow_up?: string[];
  assumptions?: string[];
  what_to_do: string[];
  what_not_to_do: string[];
  likely_conditions: string[];
  red_flags: string[];
  care_setting?: string | null;
  confidence: number;
  dataset_used: boolean;
  compliance_passed: boolean;
  audit_hash?: string | null;
  disclaimer: string;
}

function mapTriageLevel(level?: string | null): TriageLevel {
  switch (level) {
    case 'level_1':
    case 'level_2':
    case 'level_3':
    case 'level_4':
    case 'level_5':
      return level;
    case 'emergent':
    case 'emergency':
      return 'level_2';
    case 'urgent':
      return 'level_3';
    case 'routine':
    case 'less_urgent':
      return 'level_4';
    case 'self_care':
    case 'non_urgent':
      return 'level_5';
    default:
      return 'unknown';
  }
}

function mapSeverity(level: TriageLevel): TriageResponse['severity'] {
  switch (level) {
    case 'level_1':
    case 'level_2':
      return 'emergency';
    case 'level_3':
    case 'level_4':
      return 'urgent';
    case 'level_5':
      return 'self-care';
    default:
      return 'unknown';
  }
}

function mapTriageResponse(data: BackendTriageResponse): TriageResponse {
  const triageLevel = mapTriageLevel(data.triage_level);
  const needsFollowUp = Boolean(data.needs_follow_up || data.response_mode === 'follow_up');
  const assessment = data.assessment || data.response;
  const displayText = needsFollowUp ? data.response : assessment;

  return {
    id: data.audit_hash || crypto.randomUUID(),
    triageLevel,
    levelTitle: data.level_title || '',
    levelJustification: data.level_justification || '',
    severity: mapSeverity(triageLevel),
    responseMode: needsFollowUp ? 'follow_up' : 'triage_report',
    needsFollowUp,
    followUpQuestions: data.follow_up_questions || [],
    summary: displayText,
    assessment: displayText,
    reasoning: data.reasoning,
    immediateActions: data.immediate_actions || data.what_to_do || [],
    crucialWarnings: data.crucial_warnings || data.what_not_to_do || [],
    resourceRecommendations: data.resource_recommendations || [],
    requiredFollowUp: data.required_follow_up || [],
    assumptions: data.assumptions || [],
    whatToDo: data.immediate_actions || data.what_to_do || [],
    whatNotToDo: data.crucial_warnings || data.what_not_to_do || [],
    likelyConditions: data.likely_conditions || [],
    redFlags: data.red_flags || [],
    remedies: data.immediate_actions || data.what_to_do || [],
    followUp: data.routing,
    symptoms: data.symptoms,
    careSetting: data.care_setting || undefined,
    confidence: data.confidence || (data.compliance_passed ? 0.7 : 0.4),
    datasetUsed: data.dataset_used,
    createdAt: new Date().toISOString(),
    disclaimer: data.disclaimer,
  };
}

function buildTriagePayload(
  request: TriageRequest,
  options?: {
    chatId?: string;
    history?: ChatMessage[];
  }
): BackendTriageRequest {
  return {
    query: request.query || request.symptoms,
    chat_id: options?.chatId,
    conversation_history: options?.history?.map((msg) => ({
      role: msg.role,
      content: msg.content,
    })),
  };
}

function getApiBaseUrl(): string {
  return import.meta.env.VITE_API_URL || '/api/v1';
}

function mapPartialTriage(data: Record<string, unknown>): PartialTriageResponse {
  const mode = data.response_mode;
  return {
    responseMode:
      mode === 'follow_up' || mode === 'triage_report' ? mode : undefined,
    triageLevel:
      typeof data.triage_level === 'string'
        ? mapTriageLevel(data.triage_level)
        : undefined,
    levelTitle: typeof data.level_title === 'string' ? data.level_title : undefined,
    levelJustification:
      typeof data.level_justification === 'string' ? data.level_justification : undefined,
    assessment: typeof data.assessment === 'string' ? data.assessment : undefined,
    preliminaryAssessment:
      typeof data.preliminary_assessment === 'string'
        ? data.preliminary_assessment
        : undefined,
    immediateActions: Array.isArray(data.immediate_actions)
      ? data.immediate_actions.map(String)
      : undefined,
    crucialWarnings: Array.isArray(data.crucial_warnings)
      ? data.crucial_warnings.map(String)
      : undefined,
    resourceRecommendations: Array.isArray(data.resource_recommendations)
      ? data.resource_recommendations.map(String)
      : undefined,
    requiredFollowUp: Array.isArray(data.required_follow_up)
      ? data.required_follow_up.map(String)
      : undefined,
    likelyConditions: Array.isArray(data.likely_conditions)
      ? data.likely_conditions.map(String)
      : undefined,
    followUpQuestions: Array.isArray(data.follow_up_questions)
      ? data.follow_up_questions.map(String)
      : undefined,
    assumptions: Array.isArray(data.assumptions)
      ? data.assumptions.map(String)
      : undefined,
  };
}

export interface StreamTriageCallbacks {
  onStatus?: (message: string) => void;
  onPartial?: (partial: PartialTriageResponse) => void;
  onComplete?: (triage: TriageResponse) => void;
  onError?: (error: Error) => void;
}

export const triageService = {
  async submitTriage(
    request: TriageRequest,
    options?: {
      chatId?: string;
      history?: ChatMessage[];
    }
  ): Promise<TriageResponse> {
    const payload = buildTriagePayload(request, options);
    const response = await api.post<BackendTriageResponse>('/triage', payload);
    return mapTriageResponse(response.data);
  },

  async streamTriage(
    request: TriageRequest,
    callbacks: StreamTriageCallbacks,
    options?: {
      chatId?: string;
      history?: ChatMessage[];
    }
  ): Promise<TriageResponse | null> {
    const payload = buildTriagePayload(request, options);
    const streamBase =
      import.meta.env.VITE_STREAM_API_URL || getApiBaseUrl();
    const token = useAuthStore.getState().accessToken;

    const response = await fetch(`${streamBase}/triage/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Stream request failed with status ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body available for streaming');
    }

    const decoder = new TextDecoder();
    let buffer = '';
    let completed: TriageResponse | null = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const data = line.slice(6).trim();
        if (!data || data === '[DONE]') continue;

        try {
          const parsed = JSON.parse(data) as {
            type?: string;
            message?: string;
            data?: Record<string, unknown>;
            triage?: BackendTriageResponse;
          };

          if (parsed.type === 'status' && parsed.message) {
            callbacks.onStatus?.(parsed.message);
          } else if (parsed.type === 'partial' && parsed.data) {
            callbacks.onPartial?.(mapPartialTriage(parsed.data));
          } else if (parsed.type === 'done' && parsed.triage) {
            completed = mapTriageResponse(parsed.triage);
            callbacks.onComplete?.(completed);
          } else if (parsed.type === 'error') {
            throw new Error(
              typeof parsed.message === 'string' ? parsed.message : 'Stream failed'
            );
          }
        } catch (error) {
          if (!(error instanceof SyntaxError)) {
            throw error;
          }
        }
      }
    }

    return completed;
  },
};
