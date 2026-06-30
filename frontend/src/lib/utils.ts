/**
 * utils — shared utilities
 */
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merges Tailwind CSS class names, resolving conflicts.
 * Uses clsx for conditional classes and twMerge for deduplication.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format price from cents to locale string
 */
export function formatPrice(
  cents: number,
  currency: string = "EUR",
  locale: string = "es-ES"
): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(cents / 100);
}

/**
 * Format duration in minutes to "Xh Ym"
 */
export function formatDuration(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h === 0) return `${m}min`;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}min`;
}

/**
 * Calculate flight/train duration from ISO strings
 */
export function calcDurationMinutes(from: string, to: string): number {
  const diff = new Date(to).getTime() - new Date(from).getTime();
  return Math.round(diff / 60_000);
}
