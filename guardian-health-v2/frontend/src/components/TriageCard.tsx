import {
  AlertTriangle,
  HeartPulse,
  AlertOctagon,
  CheckCircle2,
  Pill,
  Stethoscope,
  ListChecks,
  FlaskConical,
  Info,
} from 'lucide-react';
import { TriageResponse } from '@/types';
import { cn } from '@/lib/utils';
import { EmergencyAlert } from './EmergencyAlert';

interface TriageCardProps {
  triage: TriageResponse;
}

const severityConfig = {
  emergency: {
    label: 'Emergency',
    color: 'text-red-700 dark:text-red-300',
    bg: 'bg-red-50 dark:bg-red-950/40',
    border: 'border-red-200 dark:border-red-900',
    icon: AlertOctagon,
    iconColor: 'text-red-600 dark:text-red-400',
    badgeBg: 'bg-red-100 dark:bg-red-900',
  },
  urgent: {
    label: 'Urgent Care',
    color: 'text-amber-700 dark:text-amber-300',
    bg: 'bg-amber-50 dark:bg-amber-950/40',
    border: 'border-amber-200 dark:border-amber-900',
    icon: AlertTriangle,
    iconColor: 'text-amber-600 dark:text-amber-400',
    badgeBg: 'bg-amber-100 dark:bg-amber-900',
  },
  'self-care': {
    label: 'Self-Care',
    color: 'text-emerald-700 dark:text-emerald-300',
    bg: 'bg-emerald-50 dark:bg-emerald-950/40',
    border: 'border-emerald-200 dark:border-emerald-900',
    icon: CheckCircle2,
    iconColor: 'text-emerald-600 dark:text-emerald-400',
    badgeBg: 'bg-emerald-100 dark:bg-emerald-900',
  },
  unknown: {
    label: 'Unknown',
    color: 'text-gray-700 dark:text-gray-300',
    bg: 'bg-gray-50 dark:bg-gray-900/40',
    border: 'border-gray-200 dark:border-gray-800',
    icon: Info,
    iconColor: 'text-gray-500 dark:text-gray-500',
    badgeBg: 'bg-gray-100 dark:bg-gray-800',
  },
};

export function TriageCard({ triage }: TriageCardProps) {
  const config = severityConfig[triage.severity] || severityConfig.unknown;
  const SeverityIcon = config.icon;

  return (
    <div className="animate-fade-in">
      {/* Emergency Alert at top if needed */}
      {triage.severity === 'emergency' && (
        <EmergencyAlert
          message="This appears to be a medical emergency. Call 911 immediately."
          onCall911={() => (window.location.href = 'tel:911')}
        />
      )}

      <div
        className={cn(
          'overflow-hidden rounded-2xl border bg-white shadow-sm dark:bg-gray-900',
          config.border
        )}
      >
        {/* Header */}
        <div className={cn('border-b px-5 py-4', config.border, config.bg)}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div
                className={cn(
                  'flex h-10 w-10 items-center justify-center rounded-xl',
                  config.badgeBg
                )}
              >
                <SeverityIcon className={cn('h-5 w-5', config.iconColor)} />
              </div>
              <div>
                <span
                  className={cn(
                    'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold',
                    config.badgeBg,
                    config.color
                  )}
                >
                  {config.label}
                </span>
                <p className="mt-0.5 text-sm font-medium text-gray-700 dark:text-gray-300">
                  {triage.summary}
                </p>
              </div>
            </div>

            {/* Confidence */}
            <div className="text-right">
              <span className="text-xs text-gray-500 dark:text-gray-500">
                Confidence
              </span>
              <div className="flex items-center gap-1">
                <FlaskConical className="h-3.5 w-3.5 text-gray-400" />
                <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                  {Math.round(triage.confidence * 100)}%
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="space-y-4 px-5 py-4">
          {/* Reasoning */}
          {triage.reasoning && (
            <div>
              <h4 className="mb-1.5 flex items-center gap-1.5 text-sm font-semibold text-gray-900 dark:text-white">
                <Stethoscope className="h-4 w-4 text-primary-500" />
                Assessment
              </h4>
              <p className="text-sm leading-relaxed text-gray-600 dark:text-gray-400">
                {triage.reasoning}
              </p>
            </div>
          )}

          {/* Symptoms Identified */}
          {triage.symptoms && triage.symptoms.length > 0 && (
            <div>
              <h4 className="mb-1.5 flex items-center gap-1.5 text-sm font-semibold text-gray-900 dark:text-white">
                <HeartPulse className="h-4 w-4 text-primary-500" />
                Identified Symptoms
              </h4>
              <div className="flex flex-wrap gap-2">
                {triage.symptoms.map((symptom, i) => (
                  <span
                    key={i}
                    className="rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-700 dark:bg-gray-800 dark:text-gray-300"
                  >
                    {symptom}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Red Flags */}
          {triage.redFlags && triage.redFlags.length > 0 && (
            <div
              className={cn(
                'rounded-xl border p-4',
                triage.severity === 'emergency'
                  ? 'border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950/30'
                  : 'border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/30'
              )}
            >
              <h4 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-red-800 dark:text-red-300">
                <AlertTriangle className="h-4 w-4" />
                Warning Signs
              </h4>
              <ul className="space-y-1.5">
                {triage.redFlags.map((flag, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-sm text-red-700 dark:text-red-400"
                  >
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-red-500" />
                    {flag}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Remedies */}
          {triage.remedies && triage.remedies.length > 0 && (
            <div>
              <h4 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-gray-900 dark:text-white">
                <Pill className="h-4 w-4 text-primary-500" />
                Recommended Actions
              </h4>
              <ul className="space-y-1.5">
                {triage.remedies.map((remedy, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400"
                  >
                    <ListChecks className="mt-0.5 h-4 w-4 shrink-0 text-primary-500" />
                    {remedy}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Follow Up */}
          {triage.followUp && (
            <div className="rounded-xl border border-primary-200 bg-primary-50 p-4 dark:border-primary-900 dark:bg-primary-950/30">
              <h4 className="mb-1 text-sm font-semibold text-primary-800 dark:text-primary-300">
                Follow-Up Guidance
              </h4>
              <p className="text-sm text-primary-700 dark:text-primary-400">
                {triage.followUp}
              </p>
            </div>
          )}

          {/* Disclaimer */}
          <div className="flex items-start gap-2 rounded-lg bg-gray-50 p-3 dark:bg-gray-800/50">
            <Info className="mt-0.5 h-4 w-4 shrink-0 text-gray-400" />
            <p className="text-xs leading-relaxed text-gray-500 dark:text-gray-500">
              {triage.disclaimer ||
                'This assessment is generated by AI and is not a substitute for professional medical advice. Always consult a qualified healthcare provider for diagnosis and treatment.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
