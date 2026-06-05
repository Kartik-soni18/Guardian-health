/** GitHub Pages project path — must match vite.config.ts `base`. */
export const GH_PAGES_BASE = '/Guardian-health';

/** App entry URL with hash routing (safe for GitHub Pages + Safari reload). */
export function appHomeUrl(): string {
  const base = import.meta.env.BASE_URL || `/${GH_PAGES_BASE}/`;
  return `${base}#/`;
}

/** Navigate to app home without leaving the project path. */
export function goToAppHome(): void {
  window.location.href = appHomeUrl();
}

/** Ensure the browser path stays under the GitHub Pages project directory. */
export function ensureProjectPath(): void {
  const path = window.location.pathname;
  if (!path.startsWith(GH_PAGES_BASE)) {
    window.location.replace(`${GH_PAGES_BASE}/`);
  }
}
