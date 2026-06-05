import { useState, useEffect, FormEvent } from 'react';
import { X, Eye, EyeOff, Loader2, Shield, Lock, User, Wand2, Copy, Check } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';
import { generateSecurePassword } from '@/lib/password';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultTab?: 'login' | 'register';
}

interface FormData {
  username: string;
  password: string;
}

interface FormErrors {
  username?: string;
  password?: string;
  general?: string;
}

export function AuthModal({ isOpen, onClose, defaultTab = 'login' }: AuthModalProps) {
  const [tab, setTab] = useState<'login' | 'register'>(defaultTab);
  const [showPassword, setShowPassword] = useState(false);
  const [passwordCopied, setPasswordCopied] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [formData, setFormData] = useState<FormData>({
    username: '',
    password: '',
  });

  const { login, register, isLoginLoading, isRegisterLoading, loginError, registerError } = useAuth();

  useEffect(() => {
    setTab(defaultTab);
  }, [defaultTab]);

  useEffect(() => {
    if (loginError) {
      const message = (loginError as Error).message || 'Login failed';
      setErrors((prev) => ({ ...prev, general: message }));
    }
    if (registerError) {
      const message = (registerError as Error).message || 'Registration failed';
      setErrors((prev) => ({ ...prev, general: message }));
    }
  }, [loginError, registerError]);

  useEffect(() => {
    if (isOpen) {
      setErrors({});
      setFormData({ username: '', password: '' });
      setPasswordCopied(false);
    }
  }, [isOpen, tab]);

  const handleGeneratePassword = () => {
    const password = generateSecurePassword();
    setFormData((prev) => ({ ...prev, password }));
    setShowPassword(true);
    setPasswordCopied(false);
  };

  const handleCopyPassword = async () => {
    if (!formData.password) return;
    try {
      await navigator.clipboard.writeText(formData.password);
    } catch {
      const textArea = document.createElement('textarea');
      textArea.value = formData.password;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
    }
    setPasswordCopied(true);
    setTimeout(() => setPasswordCopied(false), 2000);
  };

  const validatePassword = (password: string, isRegister: boolean): string | undefined => {
    if (!password) return 'Password is required';
    if (password.length < 8) return 'Password must be at least 8 characters';
    if (!isRegister) return undefined;

    const issues: string[] = [];
    if (!/[A-Z]/.test(password)) issues.push('one uppercase letter');
    if (!/[a-z]/.test(password)) issues.push('one lowercase letter');
    if (!/[0-9]/.test(password)) issues.push('one number');
    if (!/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?`~ ]/.test(password)) {
      issues.push('one special character');
    }
    if (issues.length > 0) {
      return `Password must include ${issues.join(', ')}`;
    }
    return undefined;
  };

  const validate = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.username) {
      newErrors.username = 'Username is required';
    } else if (formData.username.length < 3 || formData.username.length > 50) {
      newErrors.username = 'Username must be 3–50 characters';
    } else if (formData.username.startsWith('_') || formData.username.endsWith('_')) {
      newErrors.username = 'Username cannot start or end with an underscore';
    } else if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
      newErrors.username = 'Username can only contain letters, numbers, and underscores';
    }

    const passwordError = validatePassword(formData.password, tab === 'register');
    if (passwordError) {
      newErrors.password = passwordError;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setErrors((prev) => ({ ...prev, general: undefined }));

    if (!validate()) return;

    try {
      if (tab === 'login') {
        await login({ username: formData.username, password: formData.password });
        onClose();
      } else {
        await register({ username: formData.username, password: formData.password });
        onClose();
      }
    } catch {
      // Errors are handled via loginError/registerError effects
    }
  };

  if (!isOpen) return null;

  const isLoading = isLoginLoading || isRegisterLoading;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      <div className="relative w-full max-w-md animate-slide-up rounded-2xl bg-white shadow-2xl dark:bg-gray-900">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-lg p-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-800 dark:hover:text-gray-300"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="px-6 pt-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary-100 dark:bg-primary-950">
            <Shield className="h-6 w-6 text-primary-600 dark:text-primary-400" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            {tab === 'login' ? 'Welcome Back' : 'Create Account'}
          </h2>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {tab === 'login'
              ? 'Sign in to access your health conversations'
              : 'Join GuardianHealth for AI-powered triage'}
          </p>
        </div>

        <div className="mx-6 mt-6 flex rounded-xl bg-gray-100 p-1 dark:bg-gray-800">
          <button
            onClick={() => setTab('login')}
            className={cn(
              'flex-1 rounded-lg py-2 text-sm font-medium transition-all',
              tab === 'login'
                ? 'bg-white text-primary-700 shadow-sm dark:bg-gray-700 dark:text-primary-300'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
            )}
          >
            Log In
          </button>
          <button
            onClick={() => setTab('register')}
            className={cn(
              'flex-1 rounded-lg py-2 text-sm font-medium transition-all',
              tab === 'register'
                ? 'bg-white text-primary-700 shadow-sm dark:bg-gray-700 dark:text-primary-300'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
            )}
          >
            Sign Up
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-6">
          {errors.general && (
            <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-400">
              {errors.general}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300">
                Username
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, username: e.target.value }))
                  }
                  className={cn(
                    'w-full rounded-lg border bg-white py-2.5 pl-10 pr-4 text-sm text-gray-900 outline-none transition-all placeholder:text-gray-400 dark:bg-gray-800 dark:text-white',
                    errors.username
                      ? 'border-red-300 focus:border-red-500 focus:ring-2 focus:ring-red-200 dark:border-red-700 dark:focus:border-red-500 dark:focus:ring-red-900'
                      : 'border-gray-300 focus:border-primary-500 focus:ring-2 focus:ring-primary-200 dark:border-gray-700 dark:focus:border-primary-400 dark:focus:ring-primary-900'
                  )}
                  placeholder="your_username"
                  autoComplete="username"
                />
              </div>
              {errors.username && (
                <p className="mt-1 text-xs text-red-600 dark:text-red-400">{errors.username}</p>
              )}
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, password: e.target.value }))
                  }
                  className={cn(
                    'w-full rounded-lg border bg-white py-2.5 pl-10 pr-10 text-sm text-gray-900 outline-none transition-all placeholder:text-gray-400 dark:bg-gray-800 dark:text-white',
                    errors.password
                      ? 'border-red-300 focus:border-red-500 focus:ring-2 focus:ring-red-200 dark:border-red-700 dark:focus:border-red-500 dark:focus:ring-red-900'
                      : 'border-gray-300 focus:border-primary-500 focus:ring-2 focus:ring-primary-200 dark:border-gray-700 dark:focus:border-primary-400 dark:focus:ring-primary-900'
                  )}
                  placeholder={
                    tab === 'register'
                      ? 'Min. 8 chars, upper, lower, number, symbol'
                      : 'Your password'
                  }
                  autoComplete={tab === 'login' ? 'current-password' : 'new-password'}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-xs text-red-600 dark:text-red-400">{errors.password}</p>
              )}
              {tab === 'register' && (
                <div className="mt-2 flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleGeneratePassword}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
                  >
                    <Wand2 className="h-3.5 w-3.5" />
                    Generate password
                  </button>
                  {formData.password && (
                    <button
                      type="button"
                      onClick={handleCopyPassword}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-primary-200 bg-primary-50 px-3 py-1.5 text-xs font-medium text-primary-700 transition-colors hover:bg-primary-100 dark:border-primary-800 dark:bg-primary-950/40 dark:text-primary-300"
                    >
                      {passwordCopied ? (
                        <>
                          <Check className="h-3.5 w-3.5" />
                          Copied
                        </>
                      ) : (
                        <>
                          <Copy className="h-3.5 w-3.5" />
                          Copy password
                        </>
                      )}
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="mt-6 flex w-full items-center justify-center gap-2 rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white transition-all hover:bg-primary-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
            {tab === 'login' ? 'Log In' : 'Create Account'}
          </button>
        </form>

        <div className="border-t border-gray-200 px-6 py-4 dark:border-gray-800">
          <p className="text-center text-xs text-gray-500 dark:text-gray-400">
            By continuing, you agree to our Terms of Service and Privacy Policy.
          </p>
        </div>
      </div>
    </div>
  );
}
