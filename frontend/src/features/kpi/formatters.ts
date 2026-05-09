const ruLocale = 'ru-RU';

export function formatRub(value: number): string {
  return new Intl.NumberFormat(ruLocale, {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatLiters(value: number): string {
  return `${new Intl.NumberFormat(ruLocale, { maximumFractionDigits: 0 }).format(value)} л`;
}

export function formatPercent(value: number | null): string {
  if (value === null) {
    return '—';
  }
  return `${new Intl.NumberFormat(ruLocale, { maximumFractionDigits: 2 }).format(value)}%`;
}

export function toIsoDateInput(value: Date): string {
  const yyyy = value.getFullYear();
  const mm = String(value.getMonth() + 1).padStart(2, '0');
  const dd = String(value.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}
