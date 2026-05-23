import { mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { expect, test } from '@playwright/test';
import type { Page } from '@playwright/test';

const apiBaseUrl = process.env.FUELSIGHT_API_BASE_URL ?? 'http://localhost:8061/api/v1';
const screenshotDir = join(process.cwd(), '..', 'docs', 'screenshots');

const demoUsers = {
  admin: { email: 'admin@fuelsight.local', password: 'admin12345' },
  sales: { email: 'sales@fuelsight.local', password: 'sales12345' },
  accounting: { email: 'accounting@fuelsight.local', password: 'accounting12345' },
  analyst: { email: 'analyst@fuelsight.local', password: 'analyst12345' },
  director: { email: 'director@fuelsight.local', password: 'director12345' },
} as const;

type DemoRole = keyof typeof demoUsers;

async function resetSession(page: Page) {
  await page.context().clearCookies();
  await page.goto('/login');
  await page.evaluate(() => window.localStorage.clear());
}

async function login(page: Page, role: DemoRole, expectedUrl: RegExp = /\/dashboard/) {
  const { email, password } = demoUsers[role];
  await resetSession(page);
  await page.goto('/login');
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Пароль').fill(password);
  await page.getByRole('button', { name: 'Войти' }).click();
  await expect(page).toHaveURL(expectedUrl);
}

async function openNavPage(page: Page, navLabel: string | RegExp, headingName: string | RegExp) {
  await page.getByRole('list').getByRole('button', { name: navLabel, exact: typeof navLabel === 'string' }).click();
  await expect(page.getByRole('heading', { name: headingName }).first()).toBeVisible();
}

async function saveScreenshot(page: Page, fileName: string) {
  await page.waitForLoadState('networkidle');
  await page.screenshot({
    path: join(screenshotDir, fileName),
    fullPage: true,
  });
}

test('real-backend desktop portfolio screenshots', async ({ page, request }) => {
  mkdirSync(screenshotDir, { recursive: true });

  const healthResponse = await request.get(`${apiBaseUrl}/health`);
  expect(healthResponse.ok(), `Backend health check failed at ${apiBaseUrl}/health`).toBe(true);

  await resetSession(page);
  await page.goto('/login');
  await expect(page.getByRole('heading', { name: 'Вход в систему' })).toBeVisible();
  await saveScreenshot(page, 'desktop-login.png');

  await login(page, 'admin');
  await expect(page.getByRole('heading', { name: 'Технический обзор системы' })).toBeVisible();
  await saveScreenshot(page, 'desktop-admin-dashboard.png');

  await login(page, 'sales');
  await expect(page.getByRole('heading', { name: 'Обзор отдела продаж' })).toBeVisible();
  await saveScreenshot(page, 'desktop-sales-dashboard.png');

  await openNavPage(page, 'Импорт продаж', 'Импорт продаж');
  await saveScreenshot(page, 'desktop-sales-import.png');

  await openNavPage(page, 'Аналитика продаж', 'Аналитика продаж');
  await saveScreenshot(page, 'desktop-sales-analytics.png');

  await openNavPage(page, 'Прогноз спроса', 'Прогноз спроса');
  await page.getByRole('button', { name: 'Запустить прогноз' }).click();
  await expect(page.getByText(/Прогноз по дням|Таблица прогноза/).first()).toBeVisible();
  await saveScreenshot(page, 'desktop-forecast.png');

  await login(page, 'accounting');
  await expect(page.getByRole('heading', { name: 'Финансовый обзор' })).toBeVisible();
  await saveScreenshot(page, 'desktop-accounting-dashboard.png');

  await openNavPage(page, 'Импорт закупок', 'Импорт закупок');
  await saveScreenshot(page, 'desktop-purchase-import.png');

  await openNavPage(page, 'Финансовая сводка', 'Закупки и маржа');
  await saveScreenshot(page, 'desktop-margin-analytics.png');

  await login(page, 'analyst');
  await expect(page.getByRole('heading', { name: 'Аналитический обзор' })).toBeVisible();
  await saveScreenshot(page, 'desktop-analyst-dashboard.png');

  await openNavPage(page, 'Новости и RAG-чат', 'Сводка и чат');
  await expect(page.getByRole('heading', { name: 'Сводка и чат' })).toBeVisible();
  await expect(page.getByTestId('news-desktop-chat-pane').getByRole('heading', { name: 'Чат' })).toBeVisible();
  await saveScreenshot(page, 'desktop-news-chat.png');

  await login(page, 'director', /\/executive\/dashboard/);
  await expect(page.getByRole('heading', { name: 'Управленческая сводка' })).toBeVisible();
  await saveScreenshot(page, 'desktop-director-dashboard.png');

  await openNavPage(page, 'Управленческий отчет', 'Управленческий отчет');
  await page.getByRole('button', { name: 'Сформировать управленческий отчет' }).click();
  await expect(page.getByRole('heading', { name: 'Краткие выводы' })).toBeVisible();
  await saveScreenshot(page, 'desktop-executive-report.png');
});
