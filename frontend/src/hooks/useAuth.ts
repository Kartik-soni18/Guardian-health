import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';
import axios from 'axios';
import { authService } from '@/services/authService';
import { useAuthStore } from '@/stores/authStore';
import { goToAppHome } from '@/lib/routes';
import { LoginCredentials, RegisterData } from '@/types';

export function useAuth() {
  const queryClient = useQueryClient();
  const { user, isAuthenticated, isLoading, login, register: registerStore, logout: logoutStore, setUser, setLoading } = useAuthStore();

  const meQuery = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      const userData = await authService.getMe();
      setUser(userData);
      return userData;
    },
    enabled: isAuthenticated && !user,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  const loginMutation = useMutation({
    mutationFn: async (credentials: LoginCredentials) => {
      const response = await authService.login(credentials);
      return response;
    },
    onSuccess: (data) => {
      login(data.accessToken, data.refreshToken);
      setUser(data.user);
      queryClient.invalidateQueries({ queryKey: ['chats'] });
    },
  });

  const registerMutation = useMutation({
    mutationFn: async (data: RegisterData) => {
      const response = await authService.register(data);
      return response;
    },
    onSuccess: (data) => {
      registerStore(data.accessToken, data.refreshToken);
      setUser(data.user);
      queryClient.invalidateQueries({ queryKey: ['chats'] });
    },
  });

  const logoutMutation = useMutation({
    mutationFn: async () => {
      await authService.logout();
    },
    onSettled: () => {
      logoutStore();
      queryClient.clear();
      goToAppHome();
    },
  });

  const initAuth = useCallback(() => {
    const { accessToken, refreshToken } = useAuthStore.getState();
    if (accessToken) {
      setLoading(true);
      authService
        .getMe()
        .then((userData) => {
          if (refreshToken) {
            login(accessToken, refreshToken);
          }
          setUser(userData);
        })
        .catch((error: unknown) => {
          const status = axios.isAxiosError(error) ? error.response?.status : undefined;
          if (status === 401) {
            logoutStore();
          }
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, [setLoading, setUser, login, logoutStore]);

  return {
    user,
    isAuthenticated,
    isLoading: isLoading || meQuery.isLoading,
    login: loginMutation.mutateAsync,
    register: registerMutation.mutateAsync,
    logout: logoutMutation.mutate,
    isLoginLoading: loginMutation.isPending,
    isRegisterLoading: registerMutation.isPending,
    loginError: loginMutation.error,
    registerError: registerMutation.error,
    initAuth,
  };
}
