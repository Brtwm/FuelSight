import { API_BASE_URL } from '../config/env';
import { parseApiEnvelope } from './http';
import type {
  BacktestData,
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
  const response = await authFetch(`${API_BASE_URL}/forecasts/run`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return parseApiEnvelope<ForecastData>(response);
}

export async function fetchLatestForecast(
  authFetch: AuthFetch,
  filters: ForecastLatestFilters,
): Promise<ForecastData | null> {
  const response = await authFetch(`${API_BASE_URL}/forecasts/latest${buildLatestQuery(filters)}`, {
    method: 'GET',
  });
  return parseApiEnvelope<ForecastData | null>(response);
}

export async function runBacktest(
  authFetch: AuthFetch,
  payload: RunBacktestRequest,
): Promise<BacktestData> {
  const response = await authFetch(`${API_BASE_URL}/backtests/run`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      ...payload,
      window_type: payload.window_type ?? 'rolling',
    }),
  });
  return parseApiEnvelope<BacktestData>(response);
}

export async function fetchLatestBacktest(
  authFetch: AuthFetch,
  filters: ForecastLatestFilters,
): Promise<BacktestData | null> {
  const response = await authFetch(`${API_BASE_URL}/backtests/latest${buildLatestQuery(filters)}`, {
    method: 'GET',
  });
  return parseApiEnvelope<BacktestData | null>(response);
}

