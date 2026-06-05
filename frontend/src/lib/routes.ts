/** GitHub Pages base path — must match vite.config.ts `base`. */
export const routerBasename = import.meta.env.BASE_URL.replace(/\/$/, '') || undefined;

/** Build an in-app URL that respects the GitHub Pages base path. */
export function appUrl(path = '/'): string {
  const normalized = path.startsWith('/') ? path : `/${path}`;
  const base = import.meta.env.BASE_URL;
  if (!base || base === '/') {
    return normalized;
  }
  return `${base.replace(/\/$/, '')}${normalized}`;
}

/** Navigate to the app home (not the GitHub user root). */
export function goToAppHome(): void {
  window.location.href = appUrl('/');
}
