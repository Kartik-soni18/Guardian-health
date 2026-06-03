import { useMutation } from '@tanstack/react-query';
import { triageService } from '@/services/triageService';
import { TriageRequest, TriageResponse } from '@/types';
import { useState } from 'react';

export function useTriage() {
  const [triageResult, setTriageResult] = useState<TriageResponse | null>(null);

  const triageMutation = useMutation({
    mutationFn: async (request: TriageRequest): Promise<TriageResponse> => {
      const response = await triageService.submitTriage(request);
      return response;
    },
    onSuccess: (data) => {
      setTriageResult(data);
    },
  });

  const clearTriage = () => {
    setTriageResult(null);
    triageMutation.reset();
  };

  return {
    submitTriage: triageMutation.mutateAsync,
    triageResult,
    isLoading: triageMutation.isPending,
    error: triageMutation.error,
    clearTriage,
    isError: triageMutation.isError,
  };
}
