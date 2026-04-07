/** @vitest-environment jsdom */

import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { ApiHttpError } from '../lib/api/http';
import { ImportPage } from './ImportPage';

const authFetchMock = vi.fn();
const fetchImportJobsMock = vi.fn();
const uploadSalesFileMock = vi.fn();
const uploadPurchasesFileMock = vi.fn();
const generateHistoryDataMock = vi.fn();
const invalidateImportCachesMock = vi.fn();

vi.mock('../features/auth/AuthProvider', () => ({
  useAuth: () => ({
    authFetch: authFetchMock,
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
    fetchImportJobsMock.mockReset();
    uploadSalesFileMock.mockReset();
    uploadPurchasesFileMock.mockReset();
    generateHistoryDataMock.mockReset();
    invalidateImportCachesMock.mockReset();
    fetchImportJobsMock.mockResolvedValue([]);
    invalidateImportCachesMock.mockResolvedValue(undefined);
  });

  it('shows success message after demo-data generation', async () => {
    const user = userEvent.setup();
    generateHistoryDataMock.mockResolvedValue({
      job_id: 'job-1',
      entity_type: 'historical_data',
      status: 'queued',
    });

    renderImportPage();

    await user.click(screen.getByRole('tab', { name: 'Исторические данные' }));
    await user.click(screen.getByRole('button', { name: 'Сгенерировать' }));

    expect(await screen.findByText('Генерация запущена. Job: job-1')).toBeTruthy();
  });

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

    await user.click(screen.getByRole('tab', { name: 'Исторические данные' }));
    await user.click(screen.getByRole('button', { name: 'Сгенерировать' }));

    expect(await screen.findByText('Доступ к импорту доступен только роли admin')).toBeTruthy();
  });
});
