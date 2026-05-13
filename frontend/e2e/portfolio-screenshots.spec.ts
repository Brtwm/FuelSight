import { mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { expect, test } from '@playwright/test';
import type { Page } from '@playwright/test';

const apiBaseUrl = process.env.FUELSIGHT_API_BASE_URL ?? 'http://localhost:8061/api/v1';
const screenshotDir = join(process.cwd(), '..', 'docs', 'screenshots');

async function login(page: Page, email: string, password: string) {
  await page.goto('/login');
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Пароль').fill(password);
  await page.getByRole('button', { name: 'Войти' }).click();
  await expect(page).toHaveURL(/\/dashboard/);
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

  await page.goto('/login');
  await expect(page.getByRole('heading', { name: 'Вход в систему' })).toBeVisible();
  await saveScreenshot(page, 'desktop-login.png');

  await page.getByRole('button', { name: 'Войти' }).click();
  await expect(page.getByRole('heading', { name: 'KPI за период' })).toBeVisible();
  await saveScreenshot(page, 'desktop-dashboard.png');

  await page.getByRole('button', { name: 'Продажи', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Аналитика продаж' })).toBeVisible();
  await saveScreenshot(page, 'desktop-sales-analytics.png');

  await page.getByRole('button', { name: 'Маржа', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Закупки и маржа' })).toBeVisible();
  await saveScreenshot(page, 'desktop-margin-analytics.png');

  await page.getByRole('button', { name: 'Прогноз', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Прогноз спроса', level: 4 })).toBeVisible();
  await page.getByRole('button', { name: 'Запустить прогноз' }).click();
  await expect(page.getByText(/Прогноз по дням|Таблица прогноза/).first()).toBeVisible();
  await saveScreenshot(page, 'desktop-forecast.png');

  await page.getByRole('button', { name: 'Сводка', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Сводка и чат' })).toBeVisible();
  await expect(page.getByTestId('news-desktop-chat-pane').getByRole('heading', { name: 'Чат' })).toBeVisible();
  await saveScreenshot(page, 'desktop-news-chat.png');

  await page.getByRole('button', { name: 'Выйти' }).click();
  await login(page, 'admin@fuelsight.local', 'admin12345');
  await page.getByRole('button', { name: 'Импорт', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Начальные данные и обновления' })).toBeVisible();
  await saveScreenshot(page, 'desktop-admin-import.png');
});
