/** @vitest-environment jsdom */

import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

import { ApiHttpError } from '../lib/api/http';
import { ForecastPage } from './ForecastPage';

const useQueryMock = vi.fn();
const useMutationMock = vi.fn();
const useQueryClientMock = vi.fn();
const useMediaQueryMock = vi.fn();
const runForecastWithMetaMock = vi.fn();
const runBacktestWithMetaMock = vi.fn();
const fetchLatestForecastWithMetaMock = vi.fn();
const fetchLatestBacktestWithMetaMock = vi.fn();

vi.mock('@tanstack/react-query', async () => {
  const actual = await vi.importActual<typeof import('@tanstack/react-query')>('@tanstack/react-query');
  return {
    ...actual,
    useQuery: (...args: unknown[]) => useQueryMock(...args),
    useMutation: (...args: unknown[]) => useMutationMock(...args),
    useQueryClient: () => useQueryClientMock(),
  };
});

vi.mock('../features/auth/AuthProvider', () => ({
  useAuth: () => ({
    authFetch: vi.fn(),
    user: { role: 'admin' },
  }),
}));

vi.mock('../features/forecast/components/ForecastControlPanel', () => ({
  ForecastControlPanel: () => <div>FORECAST_CONTROL_PANEL</div>,
}));
vi.mock('../features/forecast/components/ForecastChart', () => ({
  ForecastChart: () => <div>FORECAST_CHART</div>,
}));
vi.mock('../features/forecast/components/BacktestMetricsPanel', () => ({
  BacktestMetricsPanel: () => <div>BACKTEST_METRICS_PANEL</div>,
}));
vi.mock('../features/forecast/components/ForecastDriversPanel', () => ({
  ForecastDriversPanel: () => <div>FORECAST_DRIVERS_PANEL</div>,
}));
vi.mock('../features/forecast/components/ModelHealthPanel', () => ({
  ModelHealthPanel: () => <div>MODEL_HEALTH_PANEL</div>,
}));
vi.mock('../lib/api/forecast', () => ({
  fetchLatestBacktestWithMeta: (...args: unknown[]) => fetchLatestBacktestWithMetaMock(...args),
  fetchLatestForecastWithMeta: (...args: unknown[]) => fetchLatestForecastWithMetaMock(...args),
  runBacktestWithMeta: (...args: unknown[]) => runBacktestWithMetaMock(...args),
  runForecastWithMeta: (...args: unknown[]) => runForecastWithMetaMock(...args),
}));

vi.mock('@mui/material/useMediaQuery', () => ({
  default: (...args: unknown[]) => useMediaQueryMock(...args),
}));

function queryState(overrides: Record<string, unknown> = {}) {
  return {
    isLoading: false,
    isError: false,
    data: null,
    error: null,
    refetch: vi.fn(),
    ...overrides,
  };
}

function mutationState(overrides: Record<string, unknown> = {}) {
  return {
    isPending: false,
    mutate: vi.fn(),
    mutateAsync: vi.fn(),
    error: null,
    ...overrides,
  };
}

function setupUseQueryStates(
  latestForecastState: Record<string, unknown>,
  latestBacktestState: Record<string, unknown>,
) {
  useQueryMock.mockImplementation((options: { queryKey?: unknown[] }) => {
    const queryKey = options?.queryKey ?? [];
    if (queryKey[0] === 'forecast') {
      return latestForecastState;
    }
    if (queryKey[0] === 'backtests') {
      return latestBacktestState;
    }
    return queryState();
  });
}

function setupUseMutationSequence(sequence: Array<Record<string, unknown>>) {
  let index = 0;
  useMutationMock.mockImplementation(() => {
    const current = sequence[index % sequence.length] ?? sequence[0];
    index += 1;
    return current;
  });
}

describe('ForecastPage states', () => {
  beforeEach(() => {
    useQueryMock.mockReset();
    useMutationMock.mockReset();
    useQueryClientMock.mockReset();
    runForecastWithMetaMock.mockReset();
    runBacktestWithMetaMock.mockReset();
    fetchLatestForecastWithMetaMock.mockReset();
    fetchLatestBacktestWithMetaMock.mockReset();
    useMediaQueryMock.mockReset();
    useMediaQueryMock.mockReturnValue(false);
    useQueryClientMock.mockReturnValue({
      invalidateQueries: vi.fn().mockResolvedValue(undefined),
    });
  });

  it('renders loading state', () => {
    setupUseQueryStates(queryState({ isLoading: true }), queryState());
    setupUseMutationSequence([mutationState(), mutationState()]);

    render(
      <MemoryRouter>
        <ForecastPage />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { name: 'Прогноз спроса' })).toBeTruthy();
  });

  it('renders generic error state', () => {
    setupUseQueryStates(
      queryState({ isError: true, error: new Error('boom') }),
      queryState(),
    );
    setupUseMutationSequence([mutationState(), mutationState()]);

    render(
      <MemoryRouter>
        <ForecastPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('Не удалось загрузить прогноз или backtest. Проверьте backend и повторите запрос.')).toBeTruthy();
  });

  it('renders empty state when forecast was not run yet', () => {
    setupUseQueryStates(
      queryState({ data: { data: null, meta: {} } }),
      queryState({ data: { data: null, meta: {} } }),
    );
    setupUseMutationSequence([mutationState(), mutationState()]);

    render(
      <MemoryRouter>
        <ForecastPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('Прогноз пока не запускался')).toBeTruthy();
  });

  it('renders empty state when latest forecast is scenario only', () => {
    setupUseQueryStates(
      queryState({
        data: {
          data: {
            product_code: 'AI_95',
            horizon_days: 7,
            model_type: 'catboost',
            model_status: 'active',
            scenario_name: 'what_if_price',
            scenario_params: { retail_price_delta_pct: 5 },
            forecast_points: [
              {
                target_date: '2026-04-07',
                y_hat: 12450,
                y_lo: 11900,
                y_hi: 12980,
              },
            ],
            drivers: ['Лаг 7 дней задаёт базовый тренд'],
          },
          meta: {},
        },
      }),
      queryState({ data: { data: null, meta: {} } }),
    );
    setupUseMutationSequence([mutationState(), mutationState()]);

    render(
      <MemoryRouter>
        <ForecastPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('Прогноз пока не запускался')).toBeTruthy();
    expect(screen.queryByText('FORECAST_CHART')).toBeNull();
  });

  it('renders ready state when latest payload contains base and scenario pair', () => {
    setupUseQueryStates(
      queryState({
        data: {
          data: {
            product_code: 'AI_95',
            horizon_days: 7,
            model_type: 'catboost',
            model_status: 'active',
            scenario_name: 'base',
            scenario_params: { retail_price_delta_pct: 4 },
            base_forecast_points: [
              {
                target_date: '2026-04-07',
                y_hat: 12450,
                y_lo: 11900,
                y_hi: 12980,
              },
            ],
            scenario_forecast_points: [
              {
                target_date: '2026-04-07',
                y_hat: 12110,
                y_lo: 11620,
                y_hi: 12640,
              },
            ],
            drivers: ['Лаг 7 дней задаёт базовый тренд'],
          },
          meta: {},
        },
      }),
      queryState({ data: { data: null, meta: {} } }),
    );
    setupUseMutationSequence([mutationState(), mutationState()]);

    render(
      <MemoryRouter>
        <ForecastPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('FORECAST_CHART')).toBeTruthy();
    expect(screen.queryByText('Прогноз пока не запускался')).toBeNull();
  });

  it('renders ready state and baseline fallback info', () => {
    setupUseQueryStates(
      queryState({
        data: {
          data: {
            product_code: 'AI_95',
            horizon_days: 7,
            model_type: 'seasonal_naive',
            model_status: 'baseline_fallback',
            scenario_name: 'base',
            scenario_params: null,
            forecast_points: [
              {
                target_date: '2026-04-07',
                y_hat: 12450,
                y_lo: 11900,
                y_hi: 12980,
              },
            ],
            drivers: ['Лаг 7 дней задаёт базовый тренд'],
          },
          meta: {},
        },
      }),
      queryState({
        data: {
          data: {
            product_code: 'AI_95',
            horizon_days: 7,
            model_type: 'catboost',
            window_type: 'rolling',
            metrics: { mae: 412, rmse: 553, smape: 4.8 },
            comparison: {
              seasonal_naive: { mae: 520, rmse: 690, smape: 5.8 },
              catboost: { mae: 412, rmse: 553, smape: 4.8 },
            },
            trained_at: '2026-04-06T10:00:00+00:00',
            model_version: '20260406100000',
          },
          meta: {},
        },
      }),
    );
    setupUseMutationSequence([mutationState(), mutationState()]);

    render(
      <MemoryRouter>
        <ForecastPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('FORECAST_CONTROL_PANEL')).toBeTruthy();
    expect(screen.getByText('Для выбранного горизонта нет активной модели, используется baseline_fallback.')).toBeTruthy();
    expect(screen.getByText('FORECAST_CHART')).toBeTruthy();
    expect(screen.getByText('BACKTEST_METRICS_PANEL')).toBeTruthy();
    expect(screen.getByText('FORECAST_DRIVERS_PANEL')).toBeTruthy();
  });

  it('renders insufficient-history warning for validation_error', () => {
    setupUseQueryStates(queryState({ data: null }), queryState({ data: null }));
    setupUseMutationSequence([
      mutationState({
        error: new ApiHttpError({
          status: 422,
          code: 'validation_error',
          message: 'Insufficient history for forecast',
        }),
      }),
      mutationState(),
    ]);

    render(
      <MemoryRouter>
        <ForecastPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('Истории недостаточно для расчёта прогноза и backtest. Загрузите данные или обновите начальную историю.')).toBeTruthy();
  });

  it('runs only base request when scenario delta equals zero', async () => {
    setupUseQueryStates(
      queryState({ data: { data: null, meta: {} } }),
      queryState({ data: { data: null, meta: {} } }),
    );
    const mutationOptions: Array<{ mutationFn: () => Promise<unknown> }> = [];
    useMutationMock.mockImplementation((options: { mutationFn: () => Promise<unknown> }) => {
      mutationOptions.push(options);
      return mutationState();
    });
    runForecastWithMetaMock.mockResolvedValue({ data: null, meta: {} });

    render(
      <MemoryRouter initialEntries={['/?scenario_enabled=1&retail_price_delta_pct=0']}>
        <ForecastPage />
      </MemoryRouter>,
    );

    await mutationOptions[0].mutationFn();

    expect(runForecastWithMetaMock).toHaveBeenCalledTimes(1);
    expect(runForecastWithMetaMock).toHaveBeenCalledWith(
      expect.any(Function),
      expect.objectContaining({
        product_code: expect.any(String),
        horizon_days: 7,
      }),
    );
  });

  it('renders mobile forecast card list on compact layout', () => {
    useMediaQueryMock.mockReturnValue(true);
    setupUseQueryStates(
      queryState({
        data: {
          data: {
            product_code: 'AI_95',
            horizon_days: 7,
            model_type: 'catboost',
            model_status: 'active',
            scenario_name: 'base',
            scenario_params: null,
            model_freshness: 'fresh',
            retrain_status: 'ok',
            provider_mode: 'cached',
            forecast_points: [
              {
                target_date: '2026-04-07',
                y_hat: 12450,
                y_lo: 11900,
                y_hi: 12980,
              },
            ],
            drivers: ['Лаг 7 дней задаёт базовый тренд'],
          },
          meta: {},
        },
      }),
      queryState({ data: { data: null, meta: {} } }),
    );
    setupUseMutationSequence([mutationState(), mutationState()]);

    render(
      <MemoryRouter>
        <ForecastPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('Прогноз по дням (Base vs Scenario)')).toBeTruthy();
    expect(screen.getByText(/Base:/)).toBeTruthy();
  });
});
