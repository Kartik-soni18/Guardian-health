import { StrictMode, type ReactNode } from 'react';
import { createRoot } from 'react-dom/client';
import { HashRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { App } from './App';
import { ensureProjectPath } from '@/lib/routes';
import './index.css';

ensureProjectPath();

const googleClientId = import.meta.env.VITE_CLIENT_ID_GOOGLE;

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 0,
    },
  },
});

function AppProviders({ children }: { children: ReactNode }) {
  if (!googleClientId) {
    return <>{children}</>;
  }

  return <GoogleOAuthProvider clientId={googleClientId}>{children}</GoogleOAuthProvider>;
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppProviders>
      <HashRouter>
        <QueryClientProvider client={queryClient}>
          <App />
        </QueryClientProvider>
      </HashRouter>
    </AppProviders>
  </StrictMode>,
);
