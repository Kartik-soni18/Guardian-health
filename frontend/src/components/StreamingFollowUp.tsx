import { PartialTriageResponse } from '@/types';
import { Sparkles } from 'lucide-react';

interface StreamingFollowUpProps {
  triage: PartialTriageResponse;
}

export function StreamingFollowUp({ triage }: StreamingFollowUpProps) {
  const preamble = triage.preliminaryAssessment || triage.assessment || '';
  const questions = triage.followUpQuestions || [];

  return (
    <div className="animate-fade-in">
      <div className="prose prose-sm max-w-none dark:prose-invert">
        {preamble && (
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-gray-700 dark:text-gray-300">
            {preamble}
          </p>
        )}
        {questions.length > 0 && (
          <div className="mt-3">
            <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
              To assess your situation accurately, I need a few details:
            </p>
            <ul className="mt-2 space-y-1.5">
              {questions.map((q, i) => (
                <li
                  key={i}
                  className="animate-fade-in text-sm text-gray-700 dark:text-gray-300"
                >
                  • {q}
                </li>
              ))}
            </ul>
          </div>
        )}
        <div className="mt-3 flex items-center gap-2">
          <Sparkles className="h-3.5 w-3.5 animate-pulse text-primary-500" />
          <span className="text-xs text-gray-500 dark:text-gray-400">
            Preparing follow-up questions...
          </span>
        </div>
      </div>
    </div>
  );
}
