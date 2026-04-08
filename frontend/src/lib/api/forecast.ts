import { API_BASE_URL } from '../config/env';
import { parseApiEnvelopeWithMeta } from './http';
import type { ApiResult } from './http';
import type {
  BacktestData,
  ForecastMeta,
  ForecastData,
  ForecastLatestFilters,
  RunBacktestRequest,
  RunForecastRequest,
} from './forecast.types';

type AuthFetch = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

function buildLatestQuery(filters: ForecastLatestFilters): string {
  const search = new URLSearchParams();
  search.set('product_code', filters.product_code);
  search.set('horizon_days', String(filters.horizon_days));
  return `?${search.toString()}`;
}

export async function runForecast(
  authFetch: AuthFetch,
  payload: RunForecastRequest,
): Promise<ForecastData> {
  const result = await runForecastWithMeta(authFetch, payload);
  return result.data;
}

export async function runForecastWithMeta(
  authFetch: AuthFetch,
  payload: RunForecastRequest,
): Promise<ApiResult<ForecastData, ForecastMeta>> {
  const response = await authFetch(`${API_BASE_URL}/forecasts/run`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return parseApiEnvelopeWithMeta<ForecastData, ForecastMeta>(response);
}

export async function fetchLatestForecast(
  authFetch: AuthFetch,
  filters: ForecastLatestFilters,
): Promise<ForecastData | null> {
  const result = await fetchLatestForecastWithMeta(authFetch, filters);
  return result.data;
}

export async function fetchLatestForecastWithMeta(
  authFetch: AuthFetch,
  filters: ForecastLatestFilters,
): Promise<ApiResult<ForecastData | null, ForecastMeta>> {
  const response = await authFetch(`${API_BASE_URL}/forecasts/latest${buildLatestQuery(filters)}`, {
    method: 'GET',
  });
  return parseApiEnvelopeWithMeta<ForecastData | null, ForecastMeta>(response);
}

export async function runBacktest(
  authFetch: AuthFetch,
  payload: RunBacktestRequest,
): Promise<BacktestData> {
  const result = await runBacktestWithMeta(authFetch, payload);
  return result.data;
}

export async function runBacktestWithMeta(
  authFetch: AuthFetch,
  payload: RunBacktestRequest,
): Promise<ApiResult<BacktestData, ForecastMeta>> {
  const response = await authFetch(`${API_BASE_URL}/backtests/run`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      ...payload,
      window_type: payload.window_type ?? 'rolling',
    }),
  });
  return parseApiEnvelopeWithMeta<BacktestData, ForecastMeta>(response);
}

export async function fetchLatestBacktest(
  authFetch: AuthFetch,
  filters: ForecastLatestFilters,
): Promise<BacktestData | null> {
  const result = await fetchLatestBacktestWithMeta(authFetch, filters);
  return result.data;
}

export async function fetchLatestBacktestWithMeta(
  authFetch: AuthFetch,
  filters: ForecastLatestFilters,
): Promise<ApiResult<BacktestData | null, ForecastMeta>> {
  const response = await authFetch(`${API_BASE_URL}/backtests/latest${buildLatestQuery(filters)}`, {
    method: 'GET',
  });
  return parseApiEnvelopeWithMeta<BacktestData | null, ForecastMeta>(response);
}
