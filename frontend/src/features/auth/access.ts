import type { UserRole } from '../../lib/api/auth.types';

export type RouteKey =
  | 'dashboard'
  | 'import'
  | 'importSales'
  | 'importPurchases'
  | 'importHistory'
  | 'salesAnalytics'
  | 'marginAnalytics'
  | 'forecast'
  | 'news'
  | 'reports';

export type NavigationItem = {
  labels: Partial<Record<UserRole, string>> & { default: string };
  path: string;
  paths?: Partial<Record<UserRole, string>> & { default: string };
  routeKey: RouteKey;
};

export const ROLE_LABELS: Record<UserRole, string> = {
  admin: 'Системный администратор',
  sales: 'Отдел продаж',
  accounting: 'Бухгалтерия',
  analyst: 'Аналитик',
  director: 'Генеральный директор',
};

export const ROUTE_ACCESS: Record<RouteKey, UserRole[]> = {
  dashboard: ['admin', 'sales', 'accounting', 'analyst', 'director'],
  import: ['admin', 'sales', 'accounting'],
  importSales: ['admin', 'sales'],
  importPurchases: ['admin', 'accounting'],
  importHistory: ['admin', 'sales', 'accounting'],
  salesAnalytics: ['admin', 'sales', 'analyst'],
  marginAnalytics: ['admin', 'accounting', 'analyst', 'director'],
  forecast: ['admin', 'sales', 'analyst', 'director'],
  news: ['admin', 'analyst', 'director'],
  reports: ['admin', 'analyst', 'director'],
};

export const NAVIGATION_ITEMS: NavigationItem[] = [
  {
    labels: {
      default: 'KPI',
      sales: 'Продажи',
      accounting: 'Финансовый обзор',
      director: 'Панель руководителя',
    },
    path: '/dashboard',
    routeKey: 'dashboard',
  },
  {
    labels: {
      default: 'Импорт данных',
      sales: 'Импорт продаж',
      accounting: 'Импорт закупок',
    },
    path: '/import',
    paths: {
      default: '/import/sales',
      sales: '/import/sales',
      accounting: '/import/purchases',
    },
    routeKey: 'import',
  },
  {
    labels: { default: 'Аналитика продаж' },
    path: '/analytics/sales',
    routeKey: 'salesAnalytics',
  },
  {
    labels: {
      default: 'Аналитика маржи',
      accounting: 'Финансовая сводка',
      director: 'Риски маржи',
    },
    path: '/analytics/margin',
    routeKey: 'marginAnalytics',
  },
  {
    labels: { default: 'Прогноз спроса', director: 'Сводка прогноза' },
    path: '/forecast',
    routeKey: 'forecast',
  },
  {
    labels: {
      default: 'Новости',
      analyst: 'Новости и RAG-чат',
      director: 'Новостная сводка',
    },
    path: '/news',
    routeKey: 'news',
  },
  {
    labels: { default: 'Управленческий отчет' },
    path: '/reports/executive',
    routeKey: 'reports',
  },
];

export function isAdmin(role: string | null | undefined): role is 'admin' {
  return role === 'admin';
}

export function canAccessRole(role: string | null | undefined, allowedRoles?: UserRole[]): boolean {
  if (!role) {
    return false;
  }
  if (isAdmin(role)) {
    return true;
  }
  if (!allowedRoles || allowedRoles.length === 0) {
    return true;
  }
  return allowedRoles.includes(role as UserRole);
}

export function canAccessRoute(
  role: string | null | undefined,
  routeKey: RouteKey,
): boolean {
  return canAccessRole(role, ROUTE_ACCESS[routeKey]);
}

export function getDefaultRouteForRole(role: string | null | undefined): string {
  if (role === 'director') {
    return '/executive/dashboard';
  }
  if (canAccessRoute(role, 'dashboard')) {
    return '/dashboard';
  }
  return '/dashboard';
}

export function getRouteKeyForPath(path: string): RouteKey | null {
  const pathname = path.split(/[?#]/, 1)[0] || path;
  if (pathname === '/dashboard' || pathname.startsWith('/executive/dashboard')) {
    return 'dashboard';
  }
  if (pathname === '/import') {
    return 'import';
  }
  if (pathname === '/import/sales') {
    return 'importSales';
  }
  if (pathname === '/import/purchases') {
    return 'importPurchases';
  }
  if (pathname === '/import/history') {
    return 'importHistory';
  }
  if (pathname.startsWith('/import/')) {
    return null;
  }
  const item = NAVIGATION_ITEMS.find(
    (candidate) => pathname === candidate.path || pathname.startsWith(`${candidate.path}/`),
  );
  return item?.routeKey ?? null;
}

export function canAccessPath(role: string | null | undefined, path: string): boolean {
  const routeKey = getRouteKeyForPath(path);
  return routeKey ? canAccessRoute(role, routeKey) : false;
}

export function getNavLabel(item: NavigationItem, role: UserRole | undefined): string {
  return (role ? item.labels[role] : undefined) ?? item.labels.default;
}

export function getNavPath(item: NavigationItem, role: UserRole | undefined): string {
  return (role && item.paths?.[role]) || item.paths?.default || item.path;
}
