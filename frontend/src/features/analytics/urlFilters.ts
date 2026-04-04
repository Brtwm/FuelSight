import type { AnalyticsGranularity } from '../../lib/api/analytics.types';

export type AnalyticsUrlFilters = {
  product_code: string;
  date_from: string;
  date_to: string;
  granularity: AnalyticsGranularity;
};

const ISO_DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;

export function toIsoDateInput(value: Date): string {
  const yyyy = value.getFullYear();
  const mm = String(value.getMonth() + 1).padStart(2, '0');
  const dd = String(value.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

export function buildDefaultDateRange(now: Date = new Date()): { date_from: string; date_to: string } {
  const dateTo = new Date(now);
  const dateFrom = new Date(now);
  dateFrom.setDate(dateTo.getDate() - 29);
  return {
    date_from: toIsoDateInput(dateFrom),
    date_to: toIsoDateInput(dateTo),
  };
}

function normalizeGranularity(value: string | null | undefined): AnalyticsGranularity {
  if (value === 'week' || value === 'month') {
    return value;
  }
  return 'day';
}

function normalizeDate(
  value: string | null | undefined,
  fallback: string,
): string {
  if (!value) {
    return fallback;
  }
  return ISO_DATE_PATTERN.test(value) ? value : fallback;
}

export function resolveAnalyticsFilters(
  searchParams: URLSearchParams,
  defaults: { product_code: string; date_from: string; date_to: string },
): AnalyticsUrlFilters {
  return {
    product_code: (searchParams.get('product_code') || defaults.product_code).toUpperCase(),
    date_from: normalizeDate(searchParams.get('date_from'), defaults.date_from),
    date_to: normalizeDate(searchParams.get('date_to'), defaults.date_to),
    granularity: normalizeGranularity(searchParams.get('granularity')),
  };
}

export function toSearchParams(filters: AnalyticsUrlFilters): URLSearchParams {
  const search = new URLSearchParams();
  search.set('product_code', filters.product_code);
  search.set('date_from', filters.date_from);
  search.set('date_to', filters.date_to);
  search.set('granularity', filters.granularity);
  return search;
}
