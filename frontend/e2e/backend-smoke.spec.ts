import { expect, test } from '@playwright/test';

const apiBaseUrl = process.env.FUELSIGHT_API_BASE_URL ?? 'http://localhost:8061/api/v1';

test('backend-backed browser smoke: login -> dashboard -> forecast -> news', async ({ page, request }) => {
  const healthResponse = await request.get(`${apiBaseUrl}/health`);
  expect(healthResponse.ok(), `Backend health check failed at ${apiBaseUrl}/health`).toBe(true);

  await page.goto('/login');
  await expect(page.getByLabel('Email')).toHaveValue('analyst@fuelsight.local');
  await expect(page.getByLabel('Пароль')).toHaveValue('analyst12345');
  await page.getByRole('button', { name: 'Войти' }).click();

  await expect(page).toHaveURL(/\/dashboard/);
  await expect(page.getByRole('heading', { name: 'Аналитический обзор' })).toBeVisible();

  await page.getByRole('list').getByRole('button', { name: 'Прогноз спроса', exact: true }).click();
  await expect(page).toHaveURL(/\/forecast/);
  await expect(page.getByRole('heading', { name: 'Прогноз спроса', level: 4 })).toBeVisible();
  await page.getByRole('button', { name: 'Запустить прогноз' }).click();
  await expect(page.getByText(/Прогноз по дням|Таблица прогноза/).first()).toBeVisible();

  await page.getByRole('list').getByRole('button', { name: 'Новости и RAG-чат', exact: true }).click();
  await expect(page).toHaveURL(/\/news/);
  await expect(page.getByRole('heading', { name: 'Сводка и чат' })).toBeVisible();
  await expect(page.getByTestId('news-desktop-chat-pane').getByRole('heading', { name: 'Чат' })).toBeVisible();
});
