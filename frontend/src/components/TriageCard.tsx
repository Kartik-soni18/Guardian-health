import {
  AlertTriangle,
  HeartPulse,
  AlertOctagon,
  CheckCircle2,
  ListChecks,
  FlaskConical,
  Info,
  CircleCheck,
  CircleX,
  Stethoscope,
  HelpCircle,
  ShieldAlert,
} from 'lucide-react';
import { TriageLevel, TriageResponse } from '@/types';
import { cn } from '@/lib/utils';

interface TriageCardProps {
  triage: TriageResponse;
}

const levelConfig: Record<
  TriageLevel,
  {
    label: string;
    color: string;
    bg: string;
    border: string;
    icon: typeof AlertOctagon;
    iconColor: string;
    badgeBg: string;
  }
> = {
  level_1: {
    label: 'Level 1 — Resuscitation',
    color: 'text-red-800 dark:text-red-200',
    bg: 'bg-red-50 dark:bg-red-950/40',
    border: 'border-red-300 dark:border-red-900',
    icon: AlertOctagon,
    iconColor: 'text-red-700 dark:text-red-300',
    badgeBg: 'bg-red-200 dark:bg-red-900',
  },
  level_2: {
    label: 'Level 2 — Emergent',
    color: 'text-red-700 dark:text-red-300',
    bg: 'bg-red-50 dark:bg-red-950/40',
    border: 'border-red-200 dark:border-red-900',
    icon: AlertOctagon,
    iconColor: 'text-red-600 dark:text-red-400',
    badgeBg: 'bg-red-100 dark:bg-red-900',
  },
  level_3: {
    label: 'Level 3 — Urgent',
    color: 'text-amber-700 dark:text-amber-300',
    bg: 'bg-amber-50 dark:bg-amber-950/40',
    border: 'border-amber-200 dark:border-amber-900',
    icon: AlertTriangle,
    iconColor: 'text-amber-600 dark:text-amber-400',
    badgeBg: 'bg-amber-100 dark:bg-amber-900',
  },
  level_4: {
    label: 'Level 4 — Less Urgent',
    color: 'text-blue-700 dark:text-blue-300',
    bg: 'bg-blue-50 dark:bg-blue-950/40',
    border: 'border-blue-200 dark:border-blue-900',
    icon: Info,
    iconColor: 'text-blue-600 dark:text-blue-400',
    badgeBg: 'bg-blue-100 dark:bg-blue-900',
  },
  level_5: {
    label: 'Level 5 — Non-Urgent',
    color: 'text-emerald-700 dark:text-emerald-300',
    bg: 'bg-emerald-50 dark:bg-emerald-950/40',
    border: 'border-emerald-200 dark:border-emerald-900',
    icon: CheckCircle2,
    iconColor: 'text-emerald-600 dark:text-emerald-400',
    badgeBg: 'bg-emerald-100 dark:bg-emerald-900',
  },
  unknown: {
    label: 'Clinical Guidance',
    color: 'text-gray-700 dark:text-gray-300',
    bg: 'bg-gray-50 dark:bg-gray-900/40',
    border: 'border-gray-200 dark:border-gray-800',
    icon: Info,
    iconColor: 'text-gray-500 dark:text-gray-500',
    badgeBg: 'bg-gray-100 dark:bg-gray-800',
  },
};

function ActionList({
  items,
  icon: Icon,
  title,
  className,
  itemClassName,
}: {
  items: string[];
  icon: typeof CircleCheck;
  title: string;
  className: string;
  itemClassName: string;
}) {
  if (items.length === 0) return null;
  return (
    <div className={cn('rounded-xl border p-4', className)}>
      <h4 className="mb-2 flex items-center gap-1.5 text-sm font-semibold">
        <Icon className="h-4 w-4" />
        {title}
      </h4>
      <ul className="space-y-1.5">
        {items.map((item, i) => (
          <li key={i} className={cn('flex items-start gap-2 text-sm', itemClassName)}>
            <ListChecks className="mt-0.5 h-4 w-4 shrink-0 opacity-70" />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function TriageCard({ triage }: TriageCardProps) {
  const config = levelConfig[triage.triageLevel] || levelConfig.unknown;
  const LevelIcon = config.icon;
  const displayLabel = triage.levelTitle
    ? `Level ${triage.triageLevel.replace('level_', '')} — ${triage.levelTitle}`
    : config.label;

  return (
    <div className="animate-fade-in">
      <div
        className={cn(
          'overflow-hidden rounded-2xl border bg-white shadow-sm dark:bg-gray-900',
          config.border
        )}
      >
        <div className={cn('border-b px-5 py-4', config.border, config.bg)}>
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <div className={cn('flex h-10 w-10 items-center justify-center rounded-xl', config.badgeBg)}>
                <LevelIcon className={cn('h-5 w-5', config.iconColor)} />
              </div>
              <div>
                <span
                  className={cn(
                    'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold',
                    config.badgeBg,
                    config.color
                  )}
                >
                  {displayLabel}
                </span>
                {triage.levelJustification && (
                  <p className="mt-1 text-sm italic text-gray-600 dark:text-gray-400">
                    {triage.levelJustification}
                  </p>
                )}
                <p className="mt-0.5 text-sm font-medium text-gray-700 dark:text-gray-300">
                  {triage.assessment || triage.summary}
                </p>
              </div>
            </div>
            <div className="text-right">
              <span className="text-xs text-gray-500">Confidence</span>
              <div className="flex items-center gap-1">
                <FlaskConical className="h-3.5 w-3.5 text-gray-400" />
                <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                  {Math.round(triage.confidence * 100)}%
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-4 px-5 py-4">
          {triage.likelyConditions.length > 0 && (
            <div>
              <h4 className="mb-1.5 text-sm font-semibold text-gray-900 dark:text-white">
                Possible conditions
              </h4>
              <div className="flex flex-wrap gap-2">
                {triage.likelyConditions.map((condition, i) => (
                  <span
                    key={i}
                    className="rounded-full bg-primary-50 px-2.5 py-1 text-xs font-medium text-primary-700 dark:bg-primary-950/50 dark:text-primary-300"
                  >
                    {condition}
                  </span>
                ))}
              </div>
            </div>
          )}

          {triage.symptoms.length > 0 && (
            <div>
              <h4 className="mb-1.5 flex items-center gap-1.5 text-sm font-semibold text-gray-900 dark:text-white">
                <HeartPulse className="h-4 w-4 text-primary-500" />
                Identified symptoms
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

          <ActionList
            items={triage.immediateActions}
            icon={CircleCheck}
            title="Immediate Actions (What to Do)"
            className="border-emerald-200 bg-emerald-50/60 dark:border-emerald-900 dark:bg-emerald-950/20"
            itemClassName="text-emerald-900 dark:text-emerald-200"
          />

          <ActionList
            items={triage.crucialWarnings}
            icon={CircleX}
            title="Crucial Warnings (What NOT to Do)"
            className="border-amber-200 bg-amber-50/60 dark:border-amber-900 dark:bg-amber-950/20"
            itemClassName="text-amber-900 dark:text-amber-200"
          />

          <ActionList
            items={triage.resourceRecommendations}
            icon={Stethoscope}
            title="Resource & Care Recommendations"
            className="border-blue-200 bg-blue-50/60 dark:border-blue-900 dark:bg-blue-950/20"
            itemClassName="text-blue-900 dark:text-blue-200"
          />

          <ActionList
            items={triage.requiredFollowUp}
            icon={HelpCircle}
            title="Required Follow-Up (If condition changes)"
            className="border-purple-200 bg-purple-50/60 dark:border-purple-900 dark:bg-purple-950/20"
            itemClassName="text-purple-900 dark:text-purple-200"
          />

          {triage.assumptions.length > 0 && (
            <div className="rounded-xl border border-gray-200 bg-gray-50/60 p-4 dark:border-gray-700 dark:bg-gray-900/40">
              <h4 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-gray-700 dark:text-gray-300">
                <Info className="h-4 w-4" />
                Assumptions made
              </h4>
              <ul className="space-y-1.5">
                {triage.assumptions.map((item, i) => (
                  <li key={i} className="text-sm text-gray-600 dark:text-gray-400">
                    • {item}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {triage.redFlags.length > 0 && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-950/30">
              <h4 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-red-800 dark:text-red-300">
                <ShieldAlert className="h-4 w-4" />
                Warning signs
              </h4>
              <ul className="space-y-1.5">
                {triage.redFlags.map((flag, i) => (
                  <li key={i} className="text-sm text-red-700 dark:text-red-400">
                    • {flag}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
