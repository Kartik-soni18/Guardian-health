import { PartialTriageResponse, TriageLevel } from '@/types';
import {
  ActionList,
  CircleCheck,
  CircleX,
  HelpCircle,
  Info,
  Stethoscope,
  levelConfig,
} from '@/lib/triageLevelConfig';
import { cn } from '@/lib/utils';

interface StreamingTriageCardProps {
  triage: PartialTriageResponse;
}

function resolveLevel(triage: PartialTriageResponse): TriageLevel {
  return triage.triageLevel || 'unknown';
}

export function StreamingTriageCard({ triage }: StreamingTriageCardProps) {
  const level = resolveLevel(triage);
  const config = levelConfig[level] || levelConfig.unknown;
  const LevelIcon = config.icon;
  const displayLabel = triage.levelTitle
    ? `Level ${level.replace('level_', '')} — ${triage.levelTitle}`
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
          <div className="flex items-center gap-2.5">
            <div
              className={cn(
                'flex h-10 w-10 items-center justify-center rounded-xl',
                config.badgeBg
              )}
            >
              <LevelIcon className={cn('h-5 w-5', config.iconColor)} />
            </div>
            <div className="min-w-0 flex-1">
              {triage.triageLevel ? (
                <span
                  className={cn(
                    'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold',
                    config.badgeBg,
                    config.color
                  )}
                >
                  {displayLabel}
                </span>
              ) : (
                <div className="h-5 w-40 animate-pulse rounded-full bg-gray-200 dark:bg-gray-700" />
              )}
              {triage.levelJustification ? (
                <p className="mt-1 animate-fade-in text-sm italic text-gray-600 dark:text-gray-400">
                  {triage.levelJustification}
                </p>
              ) : triage.triageLevel ? (
                <div className="mt-2 h-4 w-3/4 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
              ) : null}
              {triage.assessment ? (
                <p className="mt-1 animate-fade-in text-sm font-medium text-gray-700 dark:text-gray-300">
                  {triage.assessment}
                </p>
              ) : null}
            </div>
          </div>
        </div>

        <div className="space-y-4 px-5 py-4">
          {(triage.likelyConditions?.length ?? 0) > 0 && (
            <div className="animate-fade-in">
              <h4 className="mb-1.5 text-sm font-semibold text-gray-900 dark:text-white">
                Possible conditions
              </h4>
              <div className="flex flex-wrap gap-2">
                {triage.likelyConditions!.map((condition, i) => (
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

          <ActionList
            items={triage.immediateActions || []}
            icon={CircleCheck}
            title="Immediate Actions (What to Do)"
            className="border-emerald-200 bg-emerald-50/60 dark:border-emerald-900 dark:bg-emerald-950/20"
            itemClassName="text-emerald-900 dark:text-emerald-200"
            isStreaming
          />

          <ActionList
            items={triage.crucialWarnings || []}
            icon={CircleX}
            title="Crucial Warnings (What NOT to Do)"
            className="border-amber-200 bg-amber-50/60 dark:border-amber-900 dark:bg-amber-950/20"
            itemClassName="text-amber-900 dark:text-amber-200"
            isStreaming
          />

          <ActionList
            items={triage.resourceRecommendations || []}
            icon={Stethoscope}
            title="Resource & Care Recommendations"
            className="border-blue-200 bg-blue-50/60 dark:border-blue-900 dark:bg-blue-950/20"
            itemClassName="text-blue-900 dark:text-blue-200"
            isStreaming
          />

          <ActionList
            items={triage.requiredFollowUp || []}
            icon={HelpCircle}
            title="Required Follow-Up (If condition changes)"
            className="border-purple-200 bg-purple-50/60 dark:border-purple-900 dark:bg-purple-950/20"
            itemClassName="text-purple-900 dark:text-purple-200"
            isStreaming
          />

          {(triage.assumptions?.length ?? 0) > 0 && (
            <div className="animate-fade-in rounded-xl border border-gray-200 bg-gray-50/60 p-4 dark:border-gray-700 dark:bg-gray-900/40">
              <h4 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-gray-700 dark:text-gray-300">
                <Info className="h-4 w-4" />
                Assumptions made
              </h4>
              <ul className="space-y-1.5">
                {triage.assumptions!.map((item, i) => (
                  <li key={i} className="text-sm text-gray-600 dark:text-gray-400">
                    • {item}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex items-center gap-2 pt-1">
            <span className="h-2 w-2 animate-pulse rounded-full bg-primary-500" />
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Building your assessment...
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
