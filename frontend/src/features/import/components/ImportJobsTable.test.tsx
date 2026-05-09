/** @vitest-environment jsdom */

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ImportJobsTable } from './ImportJobsTable';
import type { ImportJob } from '../../../lib/api/import.types';

describe('ImportJobsTable', () => {
  it('renders source, quality and result labels in Russian business copy', () => {
    const job: ImportJob = {
      id: 'job-1',
      entity_type: 'sales',
      source_type: 'upload',
      file_name: 'sales.csv',
      status: 'completed',
      rows_total: 12,
      rows_success: 10,
      rows_failed: 2,
      error_report_path: null,
      started_at: '2026-04-06T10:00:00Z',
      finished_at: '2026-04-06T10:01:00Z',
      display_label: null,
      provenance_mode: 'manual_snapshot',
      quality_status: 'ok',
    };

    render(<ImportJobsTable jobs={[job]} loading={false} isError={false} />);

    expect(screen.getByText('Проверенный контур')).toBeTruthy();
    expect(screen.getByText('Данные корректные')).toBeTruthy();
    expect(screen.getByText('10 успешно / 2 с ошибкой')).toBeTruthy();
    expect(screen.queryByText('Live')).toBeNull();
    expect(screen.queryByText('OK')).toBeNull();
    expect(screen.queryByText(/ok \/ .*fail/)).toBeNull();
  });
});
