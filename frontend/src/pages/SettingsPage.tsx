import { useAuth } from '@/hooks/useAuth';
import { useThemeStore } from '@/stores/themeStore';
import { useToast } from '@/hooks/useToast';
import {
  User,
  Moon,
  Sun,
  Monitor,
  LogOut,
  Shield,
  Bell,
  Trash2,
  ChevronRight,
} from 'lucide-react';

export function SettingsPage() {
  const { user, logout, isLoading } = useAuth();
  const { mode, setMode } = useThemeStore();
  const toast = useToast();

  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully');
  };

  const handleDeleteAccount = () => {
    toast.warning('Account deletion is not yet implemented');
  };

  const themeOptions: { value: 'light' | 'dark' | 'system'; label: string; icon: typeof Sun }[] = [
    { value: 'light', label: 'Light', icon: Sun },
    { value: 'dark', label: 'Dark', icon: Moon },
    { value: 'system', label: 'System', icon: Monitor },
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-12 dark:bg-gray-950">
      <div className="mx-auto max-w-2xl px-4 sm:px-6">
        <h1 className="mb-8 text-3xl font-bold text-gray-900 dark:text-white">
          Settings
        </h1>

        {/* Account Section */}
        <div className="mb-8 rounded-2xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <div className="border-b border-gray-200 px-6 py-4 dark:border-gray-800">
            <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white">
              <User className="h-5 w-5 text-primary-600 dark:text-primary-400" />
              Account
            </h2>
          </div>

          <div className="p-6">
            {user ? (
              <div className="space-y-4">
                <div className="flex items-center gap-4">
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary-100 text-lg font-semibold text-primary-700 dark:bg-primary-950 dark:text-primary-300">
                    {user.firstName?.[0]}
                    {user.lastName?.[0]}
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-white">
                      {user.firstName} {user.lastName}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {user.email}
                    </p>
                  </div>
                </div>

                <div className="rounded-lg bg-gray-50 p-4 dark:bg-gray-800/50">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Member since
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {new Date(user.createdAt).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })}
                      </p>
                    </div>
                    <ChevronRight className="h-5 w-5 text-gray-400" />
                  </div>
                </div>

                <button
                  onClick={handleLogout}
                  disabled={isLoading}
                  className="flex w-full items-center justify-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700 transition-colors hover:bg-red-100 disabled:opacity-50 dark:border-red-900 dark:bg-red-950/30 dark:text-red-400 dark:hover:bg-red-950/50"
                >
                  <LogOut className="h-4 w-4" />
                  {isLoading ? 'Logging out...' : 'Log Out'}
                </button>
              </div>
            ) : (
              <div className="text-center py-6">
                <p className="text-gray-500 dark:text-gray-400">
                  You are not logged in.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Appearance Section */}
        <div className="mb-8 rounded-2xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <div className="border-b border-gray-200 px-6 py-4 dark:border-gray-800">
            <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white">
              <Sun className="h-5 w-5 text-primary-600 dark:text-primary-400" />
              Appearance
            </h2>
          </div>

          <div className="p-6">
            <p className="mb-4 text-sm text-gray-600 dark:text-gray-400">
              Choose your preferred theme. System will follow your device settings.
            </p>
            <div className="grid grid-cols-3 gap-3">
              {themeOptions.map((option) => {
                const Icon = option.icon;
                return (
                  <button
                    key={option.value}
                    onClick={() => setMode(option.value)}
                    className={`flex flex-col items-center gap-2 rounded-xl border-2 px-4 py-4 transition-all ${
                      mode === option.value
                        ? 'border-primary-500 bg-primary-50 dark:border-primary-400 dark:bg-primary-950/30'
                        : 'border-gray-200 bg-white hover:border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-gray-600'
                    }`}
                  >
                    <Icon
                      className={`h-6 w-6 ${
                        mode === option.value
                          ? 'text-primary-600 dark:text-primary-400'
                          : 'text-gray-500 dark:text-gray-400'
                      }`}
                    />
                    <span
                      className={`text-sm font-medium ${
                        mode === option.value
                          ? 'text-primary-700 dark:text-primary-300'
                          : 'text-gray-700 dark:text-gray-300'
                      }`}
                    >
                      {option.label}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Notifications Section */}
        <div className="mb-8 rounded-2xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <div className="border-b border-gray-200 px-6 py-4 dark:border-gray-800">
            <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white">
              <Bell className="h-5 w-5 text-primary-600 dark:text-primary-400" />
              Notifications
            </h2>
          </div>

          <div className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900 dark:text-white">
                  Push Notifications
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Receive alerts about your triage results
                </p>
              </div>
              <button
                onClick={() => toast.info('Notification preferences coming soon')}
                className="relative inline-flex h-6 w-11 items-center rounded-full bg-primary-600 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:bg-primary-500"
              >
                <span className="translate-x-6 inline-block h-4 w-4 transform rounded-full bg-white transition-transform" />
              </button>
            </div>
          </div>
        </div>

        {/* Privacy & Security */}
        <div className="mb-8 rounded-2xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <div className="border-b border-gray-200 px-6 py-4 dark:border-gray-800">
            <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white">
              <Shield className="h-5 w-5 text-primary-600 dark:text-primary-400" />
              Privacy & Security
            </h2>
          </div>

          <div className="p-6">
            <p className="mb-4 text-sm text-gray-600 dark:text-gray-400">
              Your health data is encrypted and stored securely. We never share
              your personal information with third parties.
            </p>
            <button
              onClick={() => toast.info('Privacy policy coming soon')}
              className="text-sm font-medium text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
            >
              View Privacy Policy
            </button>
          </div>
        </div>

        {/* Danger Zone */}
        {user && (
          <div className="rounded-2xl border border-red-200 bg-white shadow-sm dark:border-red-900/50 dark:bg-gray-900">
            <div className="border-b border-red-200 px-6 py-4 dark:border-red-900/50">
              <h2 className="flex items-center gap-2 text-lg font-semibold text-red-700 dark:text-red-400">
                <Trash2 className="h-5 w-5" />
                Danger Zone
              </h2>
            </div>

            <div className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    Delete Account
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Permanently delete your account and all data
                  </p>
                </div>
                <button
                  onClick={handleDeleteAccount}
                  className="rounded-lg border border-red-300 bg-white px-4 py-2 text-sm font-medium text-red-700 transition-colors hover:bg-red-50 dark:border-red-800 dark:bg-gray-800 dark:text-red-400 dark:hover:bg-red-950/30"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
