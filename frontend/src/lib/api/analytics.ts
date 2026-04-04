import { API_BASE_URL } from '../config/env';
import { parseApiEnvelope } from './http';
import type {
  AnalyticsAnomaliesFilters,
  AnalyticsAnomaly,
  MarginAnalyticsData,
  MarginAnalyticsFilters,
  SalesAnalyticsData,
  SalesAnalyticsFilters,
} from './analytics.types';

type AuthFetch = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

function buildQuery(
  filters:
    | SalesAnalyticsFilters
    | MarginAnalyticsFilters
    | AnalyticsAnomaliesFilters
    | undefined,
): string {
  const search = new URLSearchParams();
  if (!filters) {
    return '';
  }
  if (filters.product_code) {
    search.set('product_code', filters.product_code);
  }
  if (filters.date_from) {
    search.set('date_from', filters.date_from);
  }
  if (filters.date_to) {
    search.set('date_to', filters.date_to);
  }
  if ('granularity' in filters && filters.granularity) {
    search.set('granularity', filters.granularity);
  }
  if ('metric' in filters) {
    search.set('metric', filters.metric);
  }
  return search.size > 0 ? `?${search.toString()}` : '';
}

export async function fetchSalesAnalytics(
  authFetch: AuthFetch,
  filters: SalesAnalyticsFilters,
): Promise<SalesAnalyticsData> {
  const response = await authFetch(`${API_BASE_URL}/analytics/sales${buildQuery(filters)}`, {
    method: 'GET',
  });
  return parseApiEnvelope<SalesAnalyticsData>(response);
}

export async function fetchMarginAnalytics(
  authFetch: AuthFetch,
  filters: MarginAnalyticsFilters,
): Promise<MarginAnalyticsData> {
  const response = await authFetch(`${API_BASE_URL}/analytics/margin${buildQuery(filters)}`, {
    method: 'GET',
  });
  return parseApiEnvelope<MarginAnalyticsData>(response);
}

export async function fetchAnalyticsAnomalies(
  authFetch: AuthFetch,
  filters: AnalyticsAnomaliesFilters,
): Promise<AnalyticsAnomaly[]> {
  const response = await authFetch(`${API_BASE_URL}/analytics/anomalies${buildQuery(filters)}`, {
    method: 'GET',
  });
  return parseApiEnvelope<AnalyticsAnomaly[]>(response);
}
