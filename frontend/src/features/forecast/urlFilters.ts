import type { ForecastHorizonDays } from '../../lib/api/forecast.types';

export type ForecastUrlFilters = {
  product_code: string;
  horizon_days: ForecastHorizonDays;
  scenario_enabled: boolean;
  retail_price_delta_pct: number;
};

function normalizeHorizon(value: string | null): ForecastHorizonDays {
  if (value === '1' || value === '7' || value === '30') {
    return Number(value) as ForecastHorizonDays;
  }
  return 7;
}

function normalizeScenarioEnabled(value: string | null): boolean {
  return value === '1' || value === 'true';
}

function normalizeScenarioDelta(value: string | null): number {
  if (!value) {
    return 0;
  }
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return 0;
  }
  return Math.max(-40, Math.min(40, parsed));
}

export function resolveForecastFilters(
  searchParams: URLSearchParams,
  defaults: { product_code: string; horizon_days: ForecastHorizonDays },
): ForecastUrlFilters {
  return {
    product_code: (searchParams.get('product_code') || defaults.product_code).toUpperCase(),
    horizon_days: normalizeHorizon(searchParams.get('horizon_days')) || defaults.horizon_days,
    scenario_enabled: normalizeScenarioEnabled(searchParams.get('scenario_enabled')),
    retail_price_delta_pct: normalizeScenarioDelta(searchParams.get('retail_price_delta_pct')),
  };
}

export function toSearchParams(filters: ForecastUrlFilters): URLSearchParams {
  const search = new URLSearchParams();
  search.set('product_code', filters.product_code);
  search.set('horizon_days', String(filters.horizon_days));
  if (filters.scenario_enabled) {
    search.set('scenario_enabled', '1');
    search.set('retail_price_delta_pct', String(filters.retail_price_delta_pct));
  }
  return search;
}

