import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { AxiosError } from "axios";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

type FastApiErrorDetail =
  | string
  | { msg?: string; loc?: (string | number)[] }
  | Array<{ msg?: string; loc?: (string | number)[] }>;

export function parseApiError(error: unknown, fallback = "Request failed"): string {
  if (!(error instanceof AxiosError)) {
    return error instanceof Error ? error.message : fallback;
  }

  const detail = (error.response?.data as { detail?: FastApiErrorDetail } | undefined)?.detail;
  if (!detail) {
    return fallback;
  }

  if (typeof detail === "string") {
    return detail;
  }

  const items = Array.isArray(detail) ? detail : [detail];
  const messages = items
    .map((item) => {
      const raw = item.msg || "";
      return raw.replace(/^Value error,\s*/i, "").trim();
    })
    .filter(Boolean);

  return messages.length > 0 ? messages.join(" ") : fallback;
}
