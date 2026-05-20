/** @vitest-environment jsdom */

import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { ApiHttpError } from '../lib/api/http';
import { ImportPage } from './ImportPage';
import type { UserRole } from '../lib/api/auth.types';

const {
  authState,
  authFetchMock,
  fetchImportJobsMock,
  uploadSalesFileMock,
  uploadPurchasesFileMock,
  generateHistoryDataMock,
  invalidateImportCachesMock,
} = vi.hoisted(() => ({
  authState: { role: 'admin' },
  authFetchMock: vi.fn(),
  fetchImportJobsMock: vi.fn(),
  uploadSalesFileMock: vi.fn(),
  uploadPurchasesFileMock: vi.fn(),
  generateHistoryDataMock: vi.fn(),
  invalidateImportCachesMock: vi.fn(),
}));

vi.mock('../features/auth/AuthProvider', () => ({
  useAuth: () => ({
    authFetch: authFetchMock,
    user: { role: authState.role },
  }),
}));

vi.mock('../lib/api/import', () => ({
  fetchImportJobs: (...args: unknown[]) => fetchImportJobsMock(...args),
  uploadSalesFile: (...args: unknown[]) => uploadSalesFileMock(...args),
  uploadPurchasesFile: (...args: unknown[]) => uploadPurchasesFileMock(...args),
  generateHistoryData: (...args: unknown[]) => generateHistoryDataMock(...args),
}));

vi.mock('../features/import/invalidateImportCaches', () => ({
  invalidateImportCaches: (...args: unknown[]) => invalidateImportCachesMock(...args),
}));

function renderImportPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('ImportPage', () => {
  beforeEach(() => {
    authFetchMock.mockReset();
    authState.role = 'admin' satisfies UserRole;
    fetchImportJobsMock.mockReset();
    uploadSalesFileMock.mockReset();
    uploadPurchasesFileMock.mockReset();
    generateHistoryDataMock.mockReset();
    invalidateImportCachesMock.mockReset();
    fetchImportJobsMock.mockResolvedValue([]);
    invalidateImportCachesMock.mockResolvedValue(undefined);
  });

  it('shows success message after initial-history refresh request', async () => {
    generateHistoryDataMock.mockResolvedValue({
      job_id: 'job-1',
      entity_type: 'historical_data',
      status: 'queued',
      display_label: 'initial_history',
      provenance_mode: 'manual_snapshot',
      quality_status: null,
    });

    renderImportPage();

    fireEvent.click(screen.getByRole('tab', { name: 'Начальная история' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Обновить историю' }));

    expect(await screen.findByText('Обновление начальной истории запущено. Номер операции: job-1')).toBeTruthy();
  }, 20_000);

  it('shows readable admin-only error when generation is forbidden', async () => {
    const user = userEvent.setup();
    generateHistoryDataMock.mockRejectedValue(
      new ApiHttpError({
        status: 403,
        code: 'http_error',
        message: 'Forbidden',
      }),
    );

    renderImportPage();

    await user.click(screen.getByRole('tab', { name: 'Начальная история' }));
    await user.click(screen.getByRole('button', { name: 'Обновить историю' }));

    expect(await screen.findByText('У вашей роли нет доступа к этому действию импорта')).toBeTruthy();
  });

  it('hides diagnostics trigger for analyst role', () => {
    authState.role = 'analyst' satisfies UserRole;

    renderImportPage();

    expect(screen.queryByRole('button', { name: 'Диагностика' })).toBeNull();
  });

  it('shows all import actions for admin', () => {
    renderImportPage();

    expect(screen.getByRole('tab', { name: 'Продажи' })).toBeTruthy();
    expect(screen.getByRole('tab', { name: 'Закупки' })).toBeTruthy();
    expect(screen.getByRole('tab', { name: 'Начальная история' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Диагностика' })).toBeTruthy();
    expect(screen.getByText('Загрузка продаж')).toBeTruthy();
  });

  it('shows only sales upload and sales-filtered history for sales role', async () => {
    authState.role = 'sales' satisfies UserRole;

    renderImportPage();

    expect(screen.getByRole('tab', { name: 'Продажи' })).toBeTruthy();
    expect(screen.queryByRole('tab', { name: 'Закупки' })).toBeNull();
    expect(screen.queryByRole('tab', { name: 'Начальная история' })).toBeNull();
    expect(screen.getByText('Загрузка продаж')).toBeTruthy();
    expect(screen.queryByText('Загрузка закупок')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Диагностика' })).toBeNull();

    await waitFor(() => {
      expect(fetchImportJobsMock).toHaveBeenCalledWith(authFetchMock, {
        limit: 30,
        entity_type: 'sales',
      });
    });
  });

  it('shows only purchase upload and purchase-filtered history for accounting role', async () => {
    authState.role = 'accounting' satisfies UserRole;

    renderImportPage();

    expect(screen.getByRole('tab', { name: 'Закупки' })).toBeTruthy();
    expect(screen.queryByRole('tab', { name: 'Продажи' })).toBeNull();
    expect(screen.queryByRole('tab', { name: 'Начальная история' })).toBeNull();
    expect(screen.getByText('Загрузка закупок')).toBeTruthy();
    expect(screen.queryByText('Загрузка продаж')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Диагностика' })).toBeNull();

    await waitFor(() => {
      expect(fetchImportJobsMock).toHaveBeenCalledWith(authFetchMock, {
        limit: 30,
        entity_type: 'purchases',
      });
    });
  });

  it('does not fetch import history for analyst role', async () => {
    authState.role = 'analyst' satisfies UserRole;

    renderImportPage();

    expect(screen.getByText('У вашей роли нет доступа к разделу импорта.')).toBeTruthy();
    expect(screen.queryByRole('tab', { name: 'История операций' })).toBeNull();
    expect(screen.queryByRole('tab', { name: 'Продажи' })).toBeNull();
    expect(screen.queryByRole('tab', { name: 'Закупки' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Загрузить' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Обновить историю' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Диагностика' })).toBeNull();
    expect(fetchImportJobsMock).not.toHaveBeenCalled();
  });
});
