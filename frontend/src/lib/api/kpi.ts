import { API_BASE_URL } from '../config/env';
import { parseApiEnvelopeWithMeta } from './http';
import type { ApiResult } from './http';
import type {
  KpiAlert,
  KpiFilters,
  KpiSnapshotMeta,
  KpiSnapshotPoint,
  KpiSummary,
  KpiSummaryMeta,
} from './kpi.types';

type AuthFetch = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

function buildQuery(filters?: KpiFilters & { severity?: string }): string {
  const search = new URLSearchParams();
  if (filters?.date_from) {
    search.set('date_from', filters.date_from);
  }
  if (filters?.date_to) {
    search.set('date_to', filters.date_to);
  }
  if (filters?.product_code) {
    search.set('product_code', filters.product_code);
  }
  if (filters?.severity) {
    search.set('severity', filters.severity);
  }
  return search.size > 0 ? `?${search.toString()}` : '';
}

export async function fetchKpiSummary(
  authFetch: AuthFetch,
  filters?: KpiFilters,
): Promise<KpiSummary | null> {
  const result = await fetchKpiSummaryWithMeta(authFetch, filters);
  return result.data;
}

export async function fetchKpiSummaryWithMeta(
  authFetch: AuthFetch,
  filters?: KpiFilters,
): Promise<ApiResult<KpiSummary | null, KpiSummaryMeta>> {
  const response = await authFetch(`${API_BASE_URL}/kpi/summary${buildQuery(filters)}`, {
    method: 'GET',
  });
  return parseApiEnvelopeWithMeta<KpiSummary | null, KpiSummaryMeta>(response);
}

export async function fetchKpiAlerts(
  authFetch: AuthFetch,
  filters?: KpiFilters & { severity?: 'high' | 'medium' | 'low' },
): Promise<KpiAlert[]> {
  const result = await fetchKpiAlertsWithMeta(authFetch, filters);
  return result.data;
}

export async function fetchKpiAlertsWithMeta(
  authFetch: AuthFetch,
  filters?: KpiFilters & { severity?: 'high' | 'medium' | 'low' },
): Promise<ApiResult<KpiAlert[], KpiSummaryMeta>> {
  const response = await authFetch(`${API_BASE_URL}/kpi/alerts${buildQuery(filters)}`, {
    method: 'GET',
  });
  return parseApiEnvelopeWithMeta<KpiAlert[], KpiSummaryMeta>(response);
}

export async function fetchKpiSnapshot(
  authFetch: AuthFetch,
  filters?: KpiFilters,
): Promise<KpiSnapshotPoint[]> {
  const result = await fetchKpiSnapshotWithMeta(authFetch, filters);
  return result.data;
}

export async function fetchKpiSnapshotWithMeta(
  authFetch: AuthFetch,
  filters?: KpiFilters,
): Promise<ApiResult<KpiSnapshotPoint[], KpiSnapshotMeta>> {
  const response = await authFetch(`${API_BASE_URL}/kpi/snapshot${buildQuery(filters)}`, {
    method: 'GET',
  });
  return parseApiEnvelopeWithMeta<KpiSnapshotPoint[], KpiSnapshotMeta>(response);
}
