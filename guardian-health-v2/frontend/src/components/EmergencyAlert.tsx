import { Phone, AlertOctagon, MapPin, ExternalLink } from 'lucide-react';

interface EmergencyAlertProps {
  message: string;
  onCall911?: () => void;
}

export function EmergencyAlert({ message, onCall911 }: EmergencyAlertProps) {
  return (
    <div className="mb-4 animate-fade-in overflow-hidden rounded-2xl border-2 border-red-500 bg-red-600 shadow-lg dark:border-red-600 dark:bg-red-900">
      {/* Top Bar */}
      <div className="flex items-center gap-3 px-5 py-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white/20">
          <AlertOctagon className="h-6 w-6 text-white" />
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-bold text-white">Medical Emergency</h3>
          <p className="text-sm text-red-100">{message}</p>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-3 bg-red-700 px-5 py-3 dark:bg-red-950">
        <button
          onClick={onCall911}
          className="inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2.5 text-sm font-bold text-red-600 shadow-sm transition-all hover:bg-gray-100 active:scale-95"
        >
          <Phone className="h-4 w-4" />
          Call 911
        </button>

        <button
          onClick={() =>
            window.open(
              'https://www.google.com/maps/search/emergency+room+near+me',
              '_blank'
            )
          }
          className="inline-flex items-center gap-2 rounded-lg border-2 border-white/30 bg-white/10 px-4 py-2.5 text-sm font-medium text-white backdrop-blur-sm transition-all hover:bg-white/20"
        >
          <MapPin className="h-4 w-4" />
          Find ER Nearby
          <ExternalLink className="h-3 w-3 opacity-70" />
        </button>

        <button
          onClick={() =>
            window.open('tel:988')
          }
          className="inline-flex items-center gap-2 rounded-lg border-2 border-white/30 bg-white/10 px-4 py-2.5 text-sm font-medium text-white backdrop-blur-sm transition-all hover:bg-white/20"
        >
          <Phone className="h-4 w-4" />
          Suicide & Crisis: 988
        </button>
      </div>

      {/* Bottom Note */}
      <div className="bg-red-800 px-5 py-2 dark:bg-red-950">
        <p className="text-xs text-red-200">
          If you cannot safely transport yourself, call 911. Do not drive if you
          are experiencing severe symptoms.
        </p>
      </div>
    </div>
  );
}
