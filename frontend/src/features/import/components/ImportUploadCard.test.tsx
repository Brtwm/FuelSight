/** @vitest-environment jsdom */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { ImportUploadCard } from './ImportUploadCard';

describe('ImportUploadCard', () => {
  it('selects a supported file through the fallback input and submits it', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const file = new File(['date,product_code\n2026-05-01,AI_92'], 'sales.csv', { type: 'text/csv' });

    const { container } = render(<ImportUploadCard entityType="sales" loading={false} onSubmit={onSubmit} />);

    await user.upload(container.querySelector('input[type="file"]') as HTMLInputElement, file);
    expect(screen.getByText('sales.csv')).toBeTruthy();

    await user.click(screen.getByRole('button', { name: 'Загрузить' }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledWith(file, ''));
  });

  it('selects a supported file by drag-and-drop', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const file = new File(['date,product_code\n2026-05-01,AI_92'], 'sales.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    render(<ImportUploadCard entityType="sales" loading={false} onSubmit={onSubmit} />);

    const dropZone = screen.getByText('Перетащите файл сюда или выберите вручную').closest('div');
    expect(dropZone).toBeTruthy();

    fireEvent.dragOver(dropZone as HTMLElement, { dataTransfer: { files: [file] } });
    expect(screen.getByText('Отпустите файл для выбора')).toBeTruthy();

    fireEvent.drop(dropZone as HTMLElement, { dataTransfer: { files: [file] } });
    expect(screen.getByText('sales.xlsx')).toBeTruthy();
  });

  it('shows a readable error for unsupported files', () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const file = new File(['text'], 'sales.txt', { type: 'text/plain' });

    render(<ImportUploadCard entityType="sales" loading={false} onSubmit={onSubmit} />);

    const dropZone = screen.getByText('Перетащите файл сюда или выберите вручную').closest('div');
    fireEvent.drop(dropZone as HTMLElement, { dataTransfer: { files: [file] } });

    expect(screen.getByText('Поддерживаются только файлы CSV или XLSX.')).toBeTruthy();
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
