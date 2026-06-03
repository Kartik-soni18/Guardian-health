import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { ThemeMode } from '@/types';

interface ThemeState {
  mode: ThemeMode;
  resolvedMode: 'light' | 'dark';
  setMode: (mode: ThemeMode) => void;
  toggle: () => void;
}

function resolveMode(mode: ThemeMode): 'light' | 'dark' {
  if (mode === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light';
  }
  return mode;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      mode: 'system',
      resolvedMode: resolveMode('system'),

      setMode: (mode) => {
        const resolved = resolveMode(mode);
        set({ mode, resolvedMode: resolved });
        document.documentElement.classList.toggle('dark', resolved === 'dark');
      },

      toggle: () => {
        const current = get().resolvedMode;
        const next = current === 'dark' ? 'light' : 'dark';
        set({ mode: next, resolvedMode: next });
        document.documentElement.classList.toggle('dark', next === 'dark');
      },
    }),
    {
      name: 'theme-storage',
      onRehydrateStorage: () => (state) => {
        if (state) {
          const resolved = resolveMode(state.mode);
          state.resolvedMode = resolved;
          document.documentElement.classList.toggle('dark', resolved === 'dark');
        }
      },
    }
  )
);
