import { api } from './api';
import { TriageRequest, TriageResponse } from '@/types';

export const triageService = {
  async submitTriage(request: TriageRequest): Promise<TriageResponse> {
    const response = await api.post('/triage', request);
    return response.data;
  },

  async getTriageHistory(): Promise<TriageResponse[]> {
    const response = await api.get('/triage/history');
    return response.data;
  },

  async getTriageById(id: string): Promise<TriageResponse> {
    const response = await api.get(`/triage/${id}`);
    return response.data;
  },
};
