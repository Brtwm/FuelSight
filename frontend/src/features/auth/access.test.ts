import { describe, expect, it } from 'vitest';
import {
  ROLE_LABELS,
  canAccessPath,
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
    expect(canAccessRoute('sales', 'importSales')).toBe(true);
    expect(canAccessRoute('sales', 'importPurchases')).toBe(false);
    expect(canAccessRoute('sales', 'importHistory')).toBe(true);
    expect(canAccessRoute('sales', 'marginAnalytics')).toBe(false);
    expect(canAccessRoute('accounting', 'import')).toBe(true);
    expect(canAccessRoute('accounting', 'importSales')).toBe(false);
    expect(canAccessRoute('accounting', 'importPurchases')).toBe(true);
    expect(canAccessRoute('accounting', 'importHistory')).toBe(true);
    expect(canAccessRoute('accounting', 'salesAnalytics')).toBe(false);
    expect(canAccessRoute('analyst', 'import')).toBe(false);
    expect(canAccessRoute('analyst', 'importHistory')).toBe(false);
    expect(canAccessRoute('analyst', 'reports')).toBe(true);
    expect(canAccessPath('analyst', '/reports/executive')).toBe(true);
    expect(canAccessRoute('director', 'import')).toBe(false);
    expect(canAccessRoute('director', 'importSales')).toBe(false);
    expect(canAccessRoute('director', 'importPurchases')).toBe(false);
    expect(canAccessRoute('director', 'importHistory')).toBe(false);
    expect(canAccessRoute('director', 'forecast')).toBe(true);
    expect(canAccessRoute('director', 'reports')).toBe(true);
    expect(canAccessPath('director', '/reports/executive')).toBe(true);
    expect(canAccessRoute('sales', 'reports')).toBe(false);
    expect(canAccessPath('sales', '/reports/executive')).toBe(false);
    expect(canAccessRoute('accounting', 'reports')).toBe(false);
    expect(canAccessPath('accounting', '/reports/executive')).toBe(false);
    expect(getDefaultRouteForRole('director')).toBe('/executive/dashboard');
  });

  it('maps split import paths to granular route access', () => {
    expect(canAccessPath('sales', '/import/sales')).toBe(true);
    expect(canAccessPath('sales', '/import/purchases')).toBe(false);
    expect(canAccessPath('sales', '/import/history')).toBe(true);
    expect(canAccessPath('accounting', '/import/sales')).toBe(false);
    expect(canAccessPath('accounting', '/import/purchases')).toBe(true);
    expect(canAccessPath('accounting', '/import/history')).toBe(true);
    expect(canAccessPath('admin', '/import/history')).toBe(true);
    expect(canAccessPath('director', '/import/sales')).toBe(false);
    expect(canAccessPath('owner', '/import/sales')).toBe(false);
    expect(canAccessPath('admin', '/import/unknown')).toBe(false);
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
