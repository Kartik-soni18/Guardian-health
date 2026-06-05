import {
  AlertTriangle,
  AlertOctagon,
  CheckCircle2,
  Info,
  ListChecks,
  CircleCheck,
  CircleX,
  Stethoscope,
  HelpCircle,
} from 'lucide-react';
import { TriageLevel } from '@/types';
import { cn } from '@/lib/utils';

export const levelConfig: Record<
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

export function ActionList({
  items,
  icon: Icon,
  title,
  className,
  itemClassName,
  isStreaming,
}: {
  items: string[];
  icon: typeof CircleCheck;
  title: string;
  className: string;
  itemClassName: string;
  isStreaming?: boolean;
}) {
  if (items.length === 0) return null;
  return (
    <div className={cn('rounded-xl border p-4', className, isStreaming && 'animate-fade-in')}>
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

export { CircleCheck, CircleX, Stethoscope, HelpCircle, Info };
