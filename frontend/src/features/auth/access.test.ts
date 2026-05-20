import { describe, expect, it } from 'vitest';
import {
  ROLE_LABELS,
  canAccessRole,
  canAccessRoute,
  getDefaultRouteForRole,
  isAdmin,
} from './access';

describe('canAccessRole', () => {
  it('allows access when no role restriction is provided', () => {
    expect(canAccessRole('admin')).toBe(true);
    expect(canAccessRole('analyst', [])).toBe(true);
  });

  it('enforces allowed roles', () => {
    expect(canAccessRole('admin', ['admin'])).toBe(true);
    expect(canAccessRole('analyst', ['admin'])).toBe(false);
    expect(canAccessRole('sales', ['sales'])).toBe(true);
    expect(canAccessRole('accounting', ['sales'])).toBe(false);
  });

  it('keeps admin as frontend superuser', () => {
    expect(isAdmin('admin')).toBe(true);
    expect(canAccessRole('admin', ['sales'])).toBe(true);
    expect(canAccessRoute('admin', 'reports')).toBe(true);
  });

  it('denies unsupported runtime roles without admin fallback', () => {
    expect(canAccessRole('owner', ['admin'])).toBe(false);
    expect(canAccessRoute('owner', 'dashboard')).toBe(false);
    expect(getDefaultRouteForRole('owner')).toBe('/dashboard');
  });

  it('defines the Phase 3 route access matrix', () => {
    expect(canAccessRoute('sales', 'import')).toBe(true);
    expect(canAccessRoute('sales', 'marginAnalytics')).toBe(false);
    expect(canAccessRoute('accounting', 'import')).toBe(true);
    expect(canAccessRoute('accounting', 'salesAnalytics')).toBe(false);
    expect(canAccessRoute('analyst', 'import')).toBe(false);
    expect(canAccessRoute('analyst', 'reports')).toBe(true);
    expect(canAccessRoute('director', 'import')).toBe(false);
    expect(canAccessRoute('director', 'forecast')).toBe(true);
    expect(getDefaultRouteForRole('director')).toBe('/executive/dashboard');
  });

  it('has human-readable labels for all business roles', () => {
    expect(ROLE_LABELS).toEqual({
      admin: 'Системный администратор',
      sales: 'Отдел продаж',
      accounting: 'Бухгалтерия',
      analyst: 'Аналитик',
      director: 'Генеральный директор',
    });
  });
});
