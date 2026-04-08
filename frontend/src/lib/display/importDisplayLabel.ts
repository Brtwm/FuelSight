import type { DisplayLabelCode } from '../api/common.types';

const DISPLAY_LABEL_TEXT: Record<DisplayLabelCode, string> = {
  sales: 'Продажи',
  purchases: 'Закупки',
  initial_history: 'Начальная история',
};

export function formatImportDisplayLabel(
  displayLabel: DisplayLabelCode | null | undefined,
  fallback: string,
): string {
  if (!displayLabel) {
    return fallback;
  }
  return DISPLAY_LABEL_TEXT[displayLabel] ?? fallback;
}

