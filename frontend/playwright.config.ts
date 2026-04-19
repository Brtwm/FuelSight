import { defineConfig, devices } from '@playwright/test';

const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://127.0.0.1:3100';
const serverUrl = new URL(baseURL);
const serverHost = serverUrl.hostname;
const serverPort = Number(serverUrl.port || '3100');

export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  webServer: {
    command: `corepack pnpm dev --host ${serverHost} --port ${serverPort}`,
    url: baseURL,
    reuseExistingServer: true,
    timeout: 120_000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'iphone-13',
      use: { ...devices['iPhone 13'] },
    },
    {
      name: 'pixel-7',
      use: { ...devices['Pixel 7'] },
    },
  ],
});
