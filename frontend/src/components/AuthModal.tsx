import { useState, useEffect, FormEvent } from 'react';
import { X, Eye, EyeOff, Loader2, Shield, Mail, Lock, User } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultTab?: 'login' | 'register';
}

interface FormData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
}

interface FormErrors {
  email?: string;
  password?: string;
  firstName?: string;
  lastName?: string;
  general?: string;
}

export function AuthModal({ isOpen, onClose, defaultTab = 'login' }: AuthModalProps) {
  const [tab, setTab] = useState<'login' | 'register'>(defaultTab);
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [formData, setFormData] = useState<FormData>({
    email: '',
    password: '',
    firstName: '',
    lastName: '',
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
      setFormData({ email: '', password: '', firstName: '', lastName: '' });
    }
  }, [isOpen, tab]);

  const validate = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    if (tab === 'register') {
      if (!formData.firstName) {
        newErrors.firstName = 'First name is required';
      }
      if (!formData.lastName) {
        newErrors.lastName = 'Last name is required';
      }
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
        await login({ email: formData.email, password: formData.password });
        onClose();
      } else {
        await register({
          email: formData.email,
          password: formData.password,
          firstName: formData.firstName,
          lastName: formData.lastName,
        });
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
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-md animate-slide-up rounded-2xl bg-white shadow-2xl dark:bg-gray-900">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-lg p-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-800 dark:hover:text-gray-300"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Header */}
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

        {/* Tabs */}
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

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 py-6">
          {/* General Error */}
          {errors.general && (
            <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-400">
              {errors.general}
            </div>
          )}

          <div className="space-y-4">
            {/* Email */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, email: e.target.value }))
                  }
                  className={cn(
                    'w-full rounded-lg border bg-white py-2.5 pl-10 pr-4 text-sm text-gray-900 outline-none transition-all placeholder:text-gray-400 dark:bg-gray-800 dark:text-white',
                    errors.email
                      ? 'border-red-300 focus:border-red-500 focus:ring-2 focus:ring-red-200 dark:border-red-700 dark:focus:border-red-500 dark:focus:ring-red-900'
                      : 'border-gray-300 focus:border-primary-500 focus:ring-2 focus:ring-primary-200 dark:border-gray-700 dark:focus:border-primary-400 dark:focus:ring-primary-900'
                  )}
                  placeholder="you@example.com"
                />
              </div>
              {errors.email && (
                <p className="mt-1 text-xs text-red-600 dark:text-red-400">{errors.email}</p>
              )}
            </div>

            {/* Password */}
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
                  placeholder="Min. 8 characters"
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
            </div>

            {/* First Name & Last Name (register only) */}
            {tab === 'register' && (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    First Name
                  </label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      value={formData.firstName}
                      onChange={(e) =>
                        setFormData((prev) => ({ ...prev, firstName: e.target.value }))
                      }
                      className={cn(
                        'w-full rounded-lg border bg-white py-2.5 pl-10 pr-4 text-sm text-gray-900 outline-none transition-all placeholder:text-gray-400 dark:bg-gray-800 dark:text-white',
                        errors.firstName
                          ? 'border-red-300 focus:border-red-500 focus:ring-2 focus:ring-red-200 dark:border-red-700'
                          : 'border-gray-300 focus:border-primary-500 focus:ring-2 focus:ring-primary-200 dark:border-gray-700'
                      )}
                      placeholder="John"
                    />
                  </div>
                  {errors.firstName && (
                    <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                      {errors.firstName}
                    </p>
                  )}
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Last Name
                  </label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      value={formData.lastName}
                      onChange={(e) =>
                        setFormData((prev) => ({ ...prev, lastName: e.target.value }))
                      }
                      className={cn(
                        'w-full rounded-lg border bg-white py-2.5 pl-10 pr-4 text-sm text-gray-900 outline-none transition-all placeholder:text-gray-400 dark:bg-gray-800 dark:text-white',
                        errors.lastName
                          ? 'border-red-300 focus:border-red-500 focus:ring-2 focus:ring-red-200 dark:border-red-700'
                          : 'border-gray-300 focus:border-primary-500 focus:ring-2 focus:ring-primary-200 dark:border-gray-700'
                      )}
                      placeholder="Doe"
                    />
                  </div>
                  {errors.lastName && (
                    <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                      {errors.lastName}
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={isLoading}
            className="mt-6 flex w-full items-center justify-center gap-2 rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white transition-all hover:bg-primary-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
            {tab === 'login' ? 'Log In' : 'Create Account'}
          </button>
        </form>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-4 dark:border-gray-800">
          <p className="text-center text-xs text-gray-500 dark:text-gray-400">
            By continuing, you agree to our Terms of Service and Privacy Policy.
          </p>
        </div>
      </div>
    </div>
  );
}
