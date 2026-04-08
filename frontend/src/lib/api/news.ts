import { API_BASE_URL } from '../config/env';
import { parseApiEnvelopeWithMeta } from './http';
import type { ApiResult } from './http';
import type {
  DigestPeriodType,
  NewsDigestData,
  NewsDigestMeta,
  NewsRefreshMeta,
  NewsRefreshData,
  NewsSearchFilters,
  NewsSearchMeta,
  NewsSearchItem,
} from './news.types';

type AuthFetch = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

function buildSearchQuery(filters: NewsSearchFilters | undefined): string {
  const search = new URLSearchParams();
  if (!filters) {
    return '';
  }
  if (filters.q) {
    search.set('q', filters.q);
  }
  if (filters.date_from) {
    search.set('date_from', filters.date_from);
  }
  if (filters.date_to) {
    search.set('date_to', filters.date_to);
  }
  if (filters.topic) {
    search.set('topic', filters.topic);
  }
  if (filters.limit) {
    search.set('limit', String(filters.limit));
  }
  return search.size > 0 ? `?${search.toString()}` : '';
}

export async function fetchLatestNewsDigest(
  authFetch: AuthFetch,
  periodType: DigestPeriodType,
): Promise<NewsDigestData | null> {
  const result = await fetchLatestNewsDigestWithMeta(authFetch, periodType);
  return result.data;
}

export async function fetchLatestNewsDigestWithMeta(
  authFetch: AuthFetch,
  periodType: DigestPeriodType,
): Promise<ApiResult<NewsDigestData | null, NewsDigestMeta>> {
  const response = await authFetch(`${API_BASE_URL}/news/digests/latest?period_type=${periodType}`, {
    method: 'GET',
  });
  return parseApiEnvelopeWithMeta<NewsDigestData | null, NewsDigestMeta>(response);
}

export async function searchNews(
  authFetch: AuthFetch,
  filters: NewsSearchFilters,
): Promise<NewsSearchItem[]> {
  const result = await searchNewsWithMeta(authFetch, filters);
  return result.data;
}

export async function searchNewsWithMeta(
  authFetch: AuthFetch,
  filters: NewsSearchFilters,
): Promise<ApiResult<NewsSearchItem[], NewsSearchMeta>> {
  const response = await authFetch(`${API_BASE_URL}/news/search${buildSearchQuery(filters)}`, {
    method: 'GET',
  });
  return parseApiEnvelopeWithMeta<NewsSearchItem[], NewsSearchMeta>(response);
}

export async function refreshNews(authFetch: AuthFetch): Promise<NewsRefreshData> {
  const result = await refreshNewsWithMeta(authFetch);
  return result.data;
}

export async function refreshNewsWithMeta(
  authFetch: AuthFetch,
): Promise<ApiResult<NewsRefreshData, NewsRefreshMeta>> {
  const response = await authFetch(`${API_BASE_URL}/news/refresh`, {
    method: 'POST',
  });
  return parseApiEnvelopeWithMeta<NewsRefreshData, NewsRefreshMeta>(response);
}
