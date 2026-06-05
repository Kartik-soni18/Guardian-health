import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  LogIn,
  User,
  Menu,
  X,
  Shield,
  Sun,
  Moon,
  Settings,
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useThemeStore } from '@/stores/themeStore';
import { AuthModal } from './AuthModal';
import { SettingsModal } from './SettingsModal';

export function Header() {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const { resolvedMode, toggle } = useThemeStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [authTab, setAuthTab] = useState<'login' | 'register'>('login');

  return (
    <>
      <header className="sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur-md dark:border-gray-800 dark:bg-gray-950/80">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 shadow-sm">
              <Shield className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold tracking-tight text-gray-900 dark:text-white">
              Guardian<span className="text-primary-600 dark:text-primary-400">Health</span>
            </span>
          </Link>

          <div className="hidden items-center gap-2 md:flex">
            <button
              onClick={() => setSettingsOpen(true)}
              className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-white"
            >
              <Settings className="h-4 w-4" />
              Settings
            </button>

            <button
              onClick={toggle}
              className="rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-200"
              aria-label="Toggle theme"
            >
              {resolvedMode === 'dark' ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
            </button>

            {isLoading ? (
              <div className="h-9 w-20 animate-pulse rounded-lg bg-gray-200 dark:bg-gray-800" />
            ) : isAuthenticated && user ? (
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-sm font-semibold text-primary-700 dark:bg-primary-950 dark:text-primary-300">
                  {user.username[0]?.toUpperCase()}
                </div>
                <button
                  onClick={() => logout()}
                  className="rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-800"
                  title="Log out"
                >
                  <LogIn className="h-4 w-4 rotate-180" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    setAuthTab('login');
                    setAuthModalOpen(true);
                  }}
                  className="rounded-lg px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
                >
                  Log In
                </button>
                <button
                  onClick={() => {
                    setAuthTab('register');
                    setAuthModalOpen(true);
                  }}
                  className="rounded-lg bg-primary-600 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700"
                >
                  Sign Up
                </button>
              </div>
            )}
          </div>

          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="rounded-lg p-2 text-gray-500 md:hidden dark:text-gray-400"
          >
            {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {mobileMenuOpen && (
          <div className="border-t border-gray-200 bg-white px-4 py-4 md:hidden dark:border-gray-800 dark:bg-gray-950">
            <button
              onClick={() => {
                setSettingsOpen(true);
                setMobileMenuOpen(false);
              }}
              className="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium text-gray-600 dark:text-gray-400"
            >
              <Settings className="h-4 w-4" />
              Settings
            </button>

            <button
              onClick={toggle}
              className="mt-1 flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium text-gray-600 dark:text-gray-400"
            >
              {resolvedMode === 'dark' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
              {resolvedMode === 'dark' ? 'Dark Mode' : 'Light Mode'}
            </button>

            <div className="mt-4 border-t border-gray-200 pt-4 dark:border-gray-800">
              {isAuthenticated && user ? (
                <button
                  onClick={() => {
                    logout();
                    setMobileMenuOpen(false);
                  }}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium text-red-600 dark:text-red-400"
                >
                  <LogIn className="h-4 w-4 rotate-180" />
                  Log Out
                </button>
              ) : (
                <div className="space-y-2">
                  <button
                    onClick={() => {
                      setAuthTab('login');
                      setAuthModalOpen(true);
                      setMobileMenuOpen(false);
                    }}
                    className="flex w-full items-center justify-center gap-2 rounded-lg border border-gray-300 px-3 py-2.5 text-sm font-medium text-gray-700 dark:border-gray-700 dark:text-gray-300"
                  >
                    <LogIn className="h-4 w-4" />
                    Log In
                  </button>
                  <button
                    onClick={() => {
                      setAuthTab('register');
                      setAuthModalOpen(true);
                      setMobileMenuOpen(false);
                    }}
                    className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary-600 px-3 py-2.5 text-sm font-medium text-white"
                  >
                    <User className="h-4 w-4" />
                    Sign Up
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </header>

      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        defaultTab={authTab}
      />
      <SettingsModal isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </>
  );
}
