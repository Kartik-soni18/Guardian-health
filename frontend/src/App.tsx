import { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Header } from '@/components/Header';
import { ToastContainer } from '@/components/ToastContainer';
import { HomePage } from '@/pages/HomePage';
import { useAuth } from '@/hooks/useAuth';
import { useToast } from '@/hooks/useToast';

export function App() {
  const { initAuth } = useAuth();
  const toast = useToast();

  useEffect(() => {
    const handleApiError = (event: Event) => {
      const customEvent = event as CustomEvent;
      if (customEvent.detail?.message) {
        toast.error(customEvent.detail.message);
      }
    };

    window.addEventListener('api-error', handleApiError);
    return () => window.removeEventListener('api-error', handleApiError);
  }, [toast]);

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  return (
    <div className="flex min-h-screen flex-col bg-white text-gray-900 transition-colors dark:bg-gray-950 dark:text-gray-100">
      <Header />

      <main className="flex-1">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/chat" element={<Navigate to="/" replace />} />
          <Route path="/settings" element={<Navigate to="/" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      <ToastContainer />
    </div>
  );
}
