import { api } from './api';
import { Chat, ChatMessage, TriageLevel, TriageResponse } from '@/types';

interface BackendChat {
  id: string;
  title: string;
  userId: string;
  createdAt: string;
  updatedAt: string;
  messages?: BackendMessage[];
}

interface BackendMessage {
  id: string;
  chatId: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  triage?: Record<string, unknown> | null;
  createdAt: string;
}

function mapTriageLevel(level?: string | null): TriageLevel {
  switch (level) {
    case 'level_1':
    case 'level_2':
    case 'level_3':
    case 'level_4':
    case 'level_5':
      return level;
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

function mapStoredTriage(data: Record<string, unknown>): TriageResponse | null {
  if (!data || typeof data !== 'object') return null;

  const triageLevel = mapTriageLevel(
    typeof data.triage_level === 'string' ? data.triage_level : null
  );
  const needsFollowUp = Boolean(data.needs_follow_up || data.response_mode === 'follow_up');
  const assessment =
    (typeof data.assessment === 'string' ? data.assessment : '') ||
    (typeof data.response === 'string' ? data.response : '');

  return {
    id: typeof data.audit_hash === 'string' ? data.audit_hash : crypto.randomUUID(),
    triageLevel,
    levelTitle: typeof data.level_title === 'string' ? data.level_title : '',
    levelJustification:
      typeof data.level_justification === 'string' ? data.level_justification : '',
    severity: mapSeverity(triageLevel),
    responseMode: needsFollowUp ? 'follow_up' : 'triage_report',
    needsFollowUp,
    followUpQuestions: Array.isArray(data.follow_up_questions)
      ? data.follow_up_questions.map(String)
      : [],
    summary: assessment,
    assessment,
    reasoning: typeof data.reasoning === 'string' ? data.reasoning : '',
    immediateActions: Array.isArray(data.immediate_actions)
      ? data.immediate_actions.map(String)
      : [],
    crucialWarnings: Array.isArray(data.crucial_warnings)
      ? data.crucial_warnings.map(String)
      : [],
    resourceRecommendations: Array.isArray(data.resource_recommendations)
      ? data.resource_recommendations.map(String)
      : [],
    requiredFollowUp: Array.isArray(data.required_follow_up)
      ? data.required_follow_up.map(String)
      : [],
    assumptions: Array.isArray(data.assumptions) ? data.assumptions.map(String) : [],
    whatToDo: Array.isArray(data.what_to_do) ? data.what_to_do.map(String) : [],
    whatNotToDo: Array.isArray(data.what_not_to_do) ? data.what_not_to_do.map(String) : [],
    likelyConditions: Array.isArray(data.likely_conditions)
      ? data.likely_conditions.map(String)
      : [],
    redFlags: Array.isArray(data.red_flags) ? data.red_flags.map(String) : [],
    remedies: Array.isArray(data.immediate_actions) ? data.immediate_actions.map(String) : [],
    followUp: typeof data.routing === 'string' ? data.routing : '',
    symptoms: Array.isArray(data.symptoms) ? data.symptoms.map(String) : [],
    careSetting: typeof data.care_setting === 'string' ? data.care_setting : undefined,
    confidence: typeof data.confidence === 'number' ? data.confidence : 0,
    datasetUsed: Boolean(data.dataset_used),
    createdAt: new Date().toISOString(),
    disclaimer: typeof data.disclaimer === 'string' ? data.disclaimer : '',
  };
}

function mapMessage(msg: BackendMessage): ChatMessage {
  const triage =
    msg.triage && typeof msg.triage === 'object'
      ? mapStoredTriage(msg.triage)
      : null;

  return {
    id: msg.id,
    chatId: msg.chatId,
    role: msg.role,
    content: msg.content,
    triage: triage?.needsFollowUp ? null : triage,
    createdAt: msg.createdAt,
    updatedAt: msg.createdAt,
  };
}

function mapChat(chat: BackendChat): Chat {
  return {
    id: chat.id,
    title: chat.title,
    userId: chat.userId,
    createdAt: chat.createdAt,
    updatedAt: chat.updatedAt,
    messages: chat.messages?.map(mapMessage),
  };
}

export const chatService = {
  async listChats(): Promise<Chat[]> {
    const response = await api.get<BackendChat[]>('/chats');
    return response.data.map(mapChat);
  },

  async createChat(initialMessage?: string): Promise<Chat> {
    const response = await api.post<BackendChat>('/chats', {
      initialMessage,
    });
    return mapChat(response.data);
  },

  async getChat(id: string): Promise<Chat & { messages: ChatMessage[] }> {
    const response = await api.get<BackendChat>(`/chats/${id}`);
    const chat = mapChat(response.data);
    return {
      ...chat,
      messages: chat.messages || [],
    };
  },

  async deleteChat(id: string): Promise<void> {
    await api.delete(`/chats/${id}`);
  },
};
