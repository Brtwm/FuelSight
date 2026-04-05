import type { DigestPeriodType } from '../../lib/api/news.types';

export type NewsUrlFilters = {
  period_type: DigestPeriodType;
  q: string;
  date_from: string;
  date_to: string;
  topic: string;
};

const ISO_DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;

export function toIsoDateInput(value: Date): string {
  const yyyy = value.getFullYear();
  const mm = String(value.getMonth() + 1).padStart(2, '0');
  const dd = String(value.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

export function buildDefaultNewsRange(now: Date = new Date()): { date_from: string; date_to: string } {
  const dateTo = new Date(now);
  const dateFrom = new Date(now);
  dateFrom.setDate(dateTo.getDate() - 29);
  return {
    date_from: toIsoDateInput(dateFrom),
    date_to: toIsoDateInput(dateTo),
  };
}

function normalizeDate(value: string | null | undefined, fallback: string): string {
  if (!value) {
    return fallback;
  }
  return ISO_DATE_PATTERN.test(value) ? value : fallback;
}

function normalizePeriod(value: string | null | undefined): DigestPeriodType {
  if (value === 'weekly') {
    return 'weekly';
  }
  return 'daily';
}

export function resolveNewsFilters(
  searchParams: URLSearchParams,
  defaults: { date_from: string; date_to: string },
): NewsUrlFilters {
  return {
    period_type: normalizePeriod(searchParams.get('period_type')),
    q: (searchParams.get('q') || '').trim(),
    date_from: normalizeDate(searchParams.get('date_from'), defaults.date_from),
    date_to: normalizeDate(searchParams.get('date_to'), defaults.date_to),
    topic: (searchParams.get('topic') || '').trim().toLowerCase(),
  };
}

export function toSearchParams(filters: NewsUrlFilters): URLSearchParams {
  const search = new URLSearchParams();
  search.set('period_type', filters.period_type);
  search.set('date_from', filters.date_from);
  search.set('date_to', filters.date_to);
  if (filters.q) {
    search.set('q', filters.q);
  }
  if (filters.topic) {
    search.set('topic', filters.topic);
  }
  return search;
}
