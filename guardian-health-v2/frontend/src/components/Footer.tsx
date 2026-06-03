import { Shield, AlertTriangle, Heart } from 'lucide-react';

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-950">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center gap-4 md:flex-row md:justify-between">
          {/* Logo & Copyright */}
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary-600 dark:text-primary-400" />
            <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
              GuardianHealth
            </span>
            <span className="text-sm text-gray-400 dark:text-gray-600">
              &copy; {currentYear}
            </span>
          </div>

          {/* Medical Disclaimer */}
          <div className="flex max-w-xl items-start gap-2 text-center md:text-left">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" />
            <p className="text-xs leading-relaxed text-gray-500 dark:text-gray-500">
              This AI-powered triage tool provides general health information only
              and is not a substitute for professional medical advice, diagnosis, or
              treatment. Always consult a qualified healthcare provider for medical
              concerns. If you have a medical emergency, call 911 immediately.
            </p>
          </div>

          {/* Made with */}
          <div className="flex items-center gap-1.5 text-xs text-gray-400 dark:text-gray-600">
            <span>Made with</span>
            <Heart className="h-3 w-3 fill-red-400 text-red-400" />
            <span>for better health outcomes</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
