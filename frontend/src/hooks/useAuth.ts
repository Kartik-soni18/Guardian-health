import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';
import axios from 'axios';
import { authService } from '@/services/authService';
import { useAuthStore } from '@/stores/authStore';
import { goToAppHome } from '@/lib/routes';
import { isAccessTokenExpired } from '@/lib/token';
import { LoginCredentials, RegisterData } from '@/types';

export function useAuth() {
  const queryClient = useQueryClient();
  const {
    user,
    isAuthenticated,
    isLoading,
    hasHydrated,
    login,
    restoreSession,
    register: registerStore,
    logout: logoutStore,
    setUser,
    setLoading,
  } = useAuthStore();

  const meQuery = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      const userData = await authService.getMe();
      setUser(userData);
      return userData;
    },
    enabled: false,
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

  const googleLoginMutation = useMutation({
    mutationFn: async (idToken: string) => {
      const response = await authService.loginWithGoogle(idToken);
      return response;
    },
    onSuccess: (data) => {
      login(data.accessToken, data.refreshToken);
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

    if (!accessToken) {
      setLoading(false);
      return;
    }

    setLoading(true);

    const bootstrap = async () => {
      try {
        if (refreshToken && isAccessTokenExpired(accessToken)) {
          const refreshed = await authService.refreshToken(refreshToken);
          useAuthStore.getState().login(refreshed.accessToken, refreshed.refreshToken);
        }

        const userData = await authService.getMe();
        const current = useAuthStore.getState();
        restoreSession(
          current.accessToken ?? accessToken,
          current.refreshToken ?? refreshToken,
          userData,
        );
      } catch (error: unknown) {
        const status = axios.isAxiosError(error) ? error.response?.status : undefined;
        if (status === 401 || status === 403) {
          logoutStore();
        }
      } finally {
        setLoading(false);
      }
    };

    void bootstrap();
  }, [setLoading, restoreSession, logoutStore]);

  const isBootstrapping = !hasHydrated || isLoading || meQuery.isLoading;

  return {
    user,
    isAuthenticated,
    isLoading: isBootstrapping,
    login: loginMutation.mutateAsync,
    register: registerMutation.mutateAsync,
    loginWithGoogle: googleLoginMutation.mutateAsync,
    logout: logoutMutation.mutate,
    isLoginLoading: loginMutation.isPending,
    isRegisterLoading: registerMutation.isPending,
    isGoogleLoginLoading: googleLoginMutation.isPending,
    loginError: loginMutation.error,
    registerError: registerMutation.error,
    googleLoginError: googleLoginMutation.error,
    initAuth,
  };
}
