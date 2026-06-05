import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  Shield,
  Clock,
  HeartPulse,
  Brain,
  MessageSquare,
  ChevronRight,
  Stethoscope,
  AlertTriangle,
} from 'lucide-react';
import { SymptomInput } from '@/components/SymptomInput';
import { TriageCard } from '@/components/TriageCard';
import { EmergencyAlert } from '@/components/EmergencyAlert';
import { useTriage } from '@/hooks/useTriage';
import { useToast } from '@/hooks/useToast';

const features = [
  {
    icon: Brain,
    title: 'AI-Powered Analysis',
    description: 'Advanced machine learning models analyze your symptoms with clinical precision.',
  },
  {
    icon: Clock,
    title: 'Instant Results',
    description: 'Get triage recommendations in seconds, not hours. Available 24/7.',
  },
  {
    icon: Shield,
    title: 'Private & Secure',
    description: 'HIPAA-compliant encryption ensures your health data stays confidential.',
  },
  {
    icon: MessageSquare,
    title: 'Conversational Care',
    description: 'Chat naturally about your symptoms. No forms, no friction.',
  },
  {
    icon: HeartPulse,
    title: 'Evidence-Based',
    description: 'Recommendations grounded in established medical triage protocols.',
  },
  {
    icon: Stethoscope,
    title: 'Smart Escalation',
    description: 'Automatically identifies emergencies and directs you to appropriate care.',
  },
];

const suggestedPrompts = [
  'I have a severe headache with neck stiffness',
  'My child has a fever of 103°F',
  'I twisted my ankle and cannot walk on it',
  'I have chest pain that radiates to my arm',
];

export function HomePage() {
  const navigate = useNavigate();
  const { submitTriage, triageResult, isLoading, clearTriage, isError } = useTriage();
  const toast = useToast();
  const [showResult, setShowResult] = useState(false);

  const handleQuickTriage = async (symptoms: string) => {
    if (!symptoms.trim()) return;

    clearTriage();
    setShowResult(true);

    try {
      await submitTriage({ query: symptoms, symptoms });
    } catch {
      toast.error('Failed to analyze symptoms. Please try again.');
    }
  };

  const handleStartChat = (symptoms: string) => {
    navigate('/chat', { state: { initialQuery: symptoms } });
  };

  const handlePromptClick = (prompt: string) => {
    handleStartChat(prompt);
  };

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary-600 via-primary-700 to-primary-800 pb-20 pt-16 text-white dark:from-primary-900 dark:via-primary-950 dark:to-secondary-950">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -left-20 -top-20 h-96 w-96 rounded-full bg-white blur-3xl" />
          <div className="absolute -bottom-20 -right-20 h-96 w-96 rounded-full bg-secondary-400 blur-3xl" />
        </div>

        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-sm backdrop-blur-sm">
              <Activity className="h-4 w-4" />
              <span>AI-Powered Medical Triage</span>
            </div>

            <h1 className="mb-6 text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
              Get the Right Care,
              <span className="block text-secondary-300">Right Now</span>
            </h1>

            <p className="mb-10 text-lg text-primary-100 sm:text-xl">
              Describe your symptoms in plain language. Our AI triage system
              analyzes your condition and guides you to the appropriate level of care.
            </p>

            {/* Quick Triage Input */}
            <div className="mx-auto max-w-2xl">
              <div className="rounded-2xl bg-white/10 p-2 backdrop-blur-sm">
                <SymptomInput
                  onSend={handleQuickTriage}
                  placeholder="Describe your symptoms... (e.g., 'I have a headache and fever')"
                  isLoading={isLoading}
                  minRows={2}
                  showSuggestedPrompts={false}
                />
              </div>
              <p className="mt-3 text-sm text-primary-200">
                Or start a detailed conversation{' '}
                <button
                  onClick={() => navigate('/chat')}
                  className="font-medium underline underline-offset-2 hover:text-white"
                >
                  in chat
                </button>
              </p>
            </div>
          </div>
        </div>

        {/* Wave Divider */}
        <div className="absolute -bottom-1 left-0 right-0">
          <svg viewBox="0 0 1440 100" fill="none" className="w-full">
            <path
              d="M0 50C240 100 480 0 720 50C960 100 1200 0 1440 50V100H0V50Z"
              className="fill-white dark:fill-gray-950"
            />
          </svg>
        </div>
      </section>

      {/* Triage Result Section */}
      {showResult && (triageResult || isLoading || isError) && (
        <section className="mx-auto max-w-3xl px-4 py-8">
          <div className="animate-fade-in">
            {isLoading && (
              <div className="rounded-2xl border border-gray-200 bg-white p-8 text-center shadow-lg dark:border-gray-800 dark:bg-gray-900">
                <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Analyzing your symptoms...
                </h3>
                <p className="mt-2 text-gray-600 dark:text-gray-400">
                  Our AI is evaluating your condition. This takes just a moment.
                </p>
              </div>
            )}

            {isError && (
              <div className="rounded-2xl border border-red-200 bg-red-50 p-6 dark:border-red-900 dark:bg-red-950/30">
                <div className="flex items-start gap-4">
                  <AlertTriangle className="h-6 w-6 shrink-0 text-red-600 dark:text-red-400" />
                  <div>
                    <h3 className="font-semibold text-red-900 dark:text-red-100">
                      Analysis Failed
                    </h3>
                    <p className="mt-1 text-red-700 dark:text-red-300">
                      We could not analyze your symptoms at this time. Please try again
                      or start a chat for more detailed assistance.
                    </p>
                    <div className="mt-4 flex gap-3">
                      <button
                        onClick={() => {
                          clearTriage();
                          setShowResult(false);
                        }}
                        className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
                      >
                        Try Again
                      </button>
                      <button
                        onClick={() => navigate('/chat')}
                        className="rounded-lg border border-red-300 bg-white px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50 dark:border-red-700 dark:bg-transparent dark:text-red-300"
                      >
                        Go to Chat
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {triageResult && (
              <div className="space-y-4">
                {triageResult.severity === 'emergency' && (
                  <EmergencyAlert
                    message={triageResult.summary}
                    onCall911={() => window.location.href = 'tel:911'}
                  />
                )}
                <TriageCard triage={triageResult} />
                <div className="flex justify-center gap-3">
                  <button
                    onClick={() => {
                      clearTriage();
                      setShowResult(false);
                    }}
                    className="rounded-lg border border-gray-300 bg-white px-5 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
                  >
                    New Check
                  </button>
                  <button
                    onClick={() => handleStartChat(triageResult.summary)}
                    className="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-primary-700"
                  >
                    Discuss in Chat
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* Suggested Prompts */}
      {!showResult && (
        <section className="mx-auto max-w-3xl px-4 py-8">
          <h2 className="mb-4 text-center text-lg font-semibold text-gray-900 dark:text-white">
            Common Concerns
          </h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {suggestedPrompts.map((prompt, i) => (
              <button
                key={i}
                onClick={() => handlePromptClick(prompt)}
                className="group flex items-start gap-3 rounded-xl border border-gray-200 bg-white p-4 text-left shadow-sm transition-all hover:border-primary-300 hover:shadow-md dark:border-gray-800 dark:bg-gray-900 dark:hover:border-primary-700"
              >
                <MessageSquare className="mt-0.5 h-5 w-5 shrink-0 text-primary-500" />
                <span className="text-sm text-gray-700 group-hover:text-gray-900 dark:text-gray-300 dark:group-hover:text-white">
                  {prompt}
                </span>
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Features Section */}
      <section className="bg-gray-50 py-20 dark:bg-gray-900/50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
              Why GuardianHealth?
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
              Intelligent triage that puts your health first
            </p>
          </div>

          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="group rounded-2xl border border-gray-200 bg-white p-6 shadow-sm transition-all hover:border-primary-200 hover:shadow-md dark:border-gray-800 dark:bg-gray-900 dark:hover:border-primary-800"
              >
                <div className="mb-4 inline-flex rounded-xl bg-primary-50 p-3 dark:bg-primary-950/50">
                  <feature.icon className="h-6 w-6 text-primary-600 dark:text-primary-400" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-gray-900 dark:text-white">
                  {feature.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="mx-auto max-w-4xl px-4 text-center sm:px-6">
          <h2 className="mb-4 text-3xl font-bold text-gray-900 dark:text-white">
            Not Sure Where to Start?
          </h2>
          <p className="mb-8 text-lg text-gray-600 dark:text-gray-400">
            Chat with our AI assistant. Describe how you are feeling and get
            personalized guidance.
          </p>
          <button
            onClick={() => navigate('/chat')}
            className="inline-flex items-center gap-2 rounded-xl bg-primary-600 px-8 py-4 text-lg font-semibold text-white shadow-lg transition-all hover:bg-primary-700 hover:shadow-xl"
          >
            <MessageSquare className="h-5 w-5" />
            Start Chatting
          </button>
        </div>
      </section>

      {/* Disclaimer */}
      <section className="border-t border-gray-200 bg-gray-50 py-12 dark:border-gray-800 dark:bg-gray-950">
        <div className="mx-auto max-w-3xl px-4 text-center">
          <div className="flex items-center justify-center gap-2 text-amber-600 dark:text-amber-400">
            <AlertTriangle className="h-5 w-5" />
            <span className="font-semibold">Medical Disclaimer</span>
          </div>
          <p className="mt-4 text-sm leading-relaxed text-gray-600 dark:text-gray-400">
            GuardianHealth is an AI-powered triage tool designed to provide general
            health information and guidance. It is not a substitute for professional
            medical advice, diagnosis, or treatment. Always seek the advice of your
            physician or other qualified health provider with any questions you may
            have regarding a medical condition. If you are experiencing a medical
            emergency, call 911 or your local emergency services immediately.
          </p>
        </div>
      </section>
    </div>
  );
}
