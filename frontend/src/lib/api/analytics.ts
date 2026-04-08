import { API_BASE_URL } from '../config/env';
import { parseApiEnvelopeWithMeta } from './http';
import type { ApiResult } from './http';
import type {
  AnalyticsAnomaliesMeta,
  AnalyticsAnomaliesFilters,
  AnalyticsAnomaly,
  MarginAnalyticsMeta,
  MarginAnalyticsData,
  MarginAnalyticsFilters,
  SalesAnalyticsMeta,
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
  const result = await fetchSalesAnalyticsWithMeta(authFetch, filters);
  return result.data;
}

export async function fetchSalesAnalyticsWithMeta(
  authFetch: AuthFetch,
  filters: SalesAnalyticsFilters,
): Promise<ApiResult<SalesAnalyticsData, SalesAnalyticsMeta>> {
  const response = await authFetch(`${API_BASE_URL}/analytics/sales${buildQuery(filters)}`, {
    method: 'GET',
  });
  return parseApiEnvelopeWithMeta<SalesAnalyticsData, SalesAnalyticsMeta>(response);
}

export async function fetchMarginAnalytics(
  authFetch: AuthFetch,
  filters: MarginAnalyticsFilters,
): Promise<MarginAnalyticsData> {
  const result = await fetchMarginAnalyticsWithMeta(authFetch, filters);
  return result.data;
}

export async function fetchMarginAnalyticsWithMeta(
  authFetch: AuthFetch,
  filters: MarginAnalyticsFilters,
): Promise<ApiResult<MarginAnalyticsData, MarginAnalyticsMeta>> {
  const response = await authFetch(`${API_BASE_URL}/analytics/margin${buildQuery(filters)}`, {
    method: 'GET',
  });
  return parseApiEnvelopeWithMeta<MarginAnalyticsData, MarginAnalyticsMeta>(response);
}

export async function fetchAnalyticsAnomalies(
  authFetch: AuthFetch,
  filters: AnalyticsAnomaliesFilters,
): Promise<AnalyticsAnomaly[]> {
  const result = await fetchAnalyticsAnomaliesWithMeta(authFetch, filters);
  return result.data;
}

export async function fetchAnalyticsAnomaliesWithMeta(
  authFetch: AuthFetch,
  filters: AnalyticsAnomaliesFilters,
): Promise<ApiResult<AnalyticsAnomaly[], AnalyticsAnomaliesMeta>> {
  const response = await authFetch(`${API_BASE_URL}/analytics/anomalies${buildQuery(filters)}`, {
    method: 'GET',
  });
  return parseApiEnvelopeWithMeta<AnalyticsAnomaly[], AnalyticsAnomaliesMeta>(response);
}
