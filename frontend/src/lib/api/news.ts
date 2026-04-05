import { API_BASE_URL } from '../config/env';
import { parseApiEnvelope } from './http';
import type {
  DigestPeriodType,
  NewsDigestData,
  NewsRefreshData,
  NewsSearchFilters,
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
  const response = await authFetch(`${API_BASE_URL}/news/digests/latest?period_type=${periodType}`, {
    method: 'GET',
  });
  return parseApiEnvelope<NewsDigestData | null>(response);
}

export async function searchNews(
  authFetch: AuthFetch,
  filters: NewsSearchFilters,
): Promise<NewsSearchItem[]> {
  const response = await authFetch(`${API_BASE_URL}/news/search${buildSearchQuery(filters)}`, {
    method: 'GET',
  });
  return parseApiEnvelope<NewsSearchItem[]>(response);
}

export async function refreshNews(authFetch: AuthFetch): Promise<NewsRefreshData> {
  const response = await authFetch(`${API_BASE_URL}/news/refresh`, {
    method: 'POST',
  });
  return parseApiEnvelope<NewsRefreshData>(response);
}
