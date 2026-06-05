import { useEffect } from 'react';

export function MaintenancePage() {
  useEffect(() => {
    document.title = 'GuardianHealth — Development in Progress';
    const meta = document.querySelector('meta[name="description"]');
    if (meta) {
      meta.setAttribute(
        'content',
        'GuardianHealth is being redesigned. The site will return soon.',
      );
    }
  }, []);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-teal-50 via-white to-emerald-50 px-6 text-gray-900 dark:from-gray-950 dark:via-gray-900 dark:to-teal-950 dark:text-gray-100">
      <div className="w-full max-w-lg rounded-2xl border border-teal-100 bg-white/80 p-10 text-center shadow-xl backdrop-blur dark:border-teal-900/50 dark:bg-gray-900/80">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-teal-100 dark:bg-teal-900/40">
          <svg
            className="h-8 w-8 text-teal-700 dark:text-teal-300"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M11.42 15.17 17.25 21A2.652 2.652 0 0 0 21 17.25l-5.877-5.877M11.42 15.17l2.496-3.03c.317-.384.74-.626 1.208-.766M11.42 15.17l-4.655 5.653a2.548 2.548 0 1 1-3.586-3.586l4.655-5.653m3.66 2.496-3.03-2.496"
            />
          </svg>
        </div>

        <p className="mb-2 text-sm font-semibold uppercase tracking-widest text-teal-700 dark:text-teal-400">
          GuardianHealth
        </p>
        <h1 className="mb-4 text-3xl font-bold tracking-tight">
          Development in Progress
        </h1>
        <p className="mb-6 text-base leading-relaxed text-gray-600 dark:text-gray-300">
          We&apos;re redesigning the platform to improve reliability and the
          triage experience. The live app is temporarily unavailable while we
          rebuild.
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Check back soon — thank you for your patience.
        </p>
      </div>
    </div>
  );
}
