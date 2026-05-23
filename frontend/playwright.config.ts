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
      name: 'desktop-analyst',
      testMatch: /analyst-first-flow\.spec\.ts/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'desktop-admin',
      testMatch: /admin-operational-flow\.spec\.ts/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'backend-smoke',
      testMatch: /backend-smoke\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        baseURL: process.env.PLAYWRIGHT_BACKEND_BASE_URL ?? 'http://127.0.0.1:3000',
      },
    },
    {
      name: 'portfolio-screenshots',
      testMatch: /portfolio-screenshots\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        baseURL: process.env.PLAYWRIGHT_BACKEND_BASE_URL ?? 'http://127.0.0.1:3000',
        viewport: { width: 1440, height: 1000 },
        deviceScaleFactor: 1,
      },
    },
    {
      name: 'mobile-iphone-13',
      testMatch: /mobile-smoke\.spec\.ts/,
      use: { ...devices['iPhone 13'] },
    },
    {
      name: 'mobile-pixel-7',
      testMatch: /mobile-smoke\.spec\.ts/,
      use: { ...devices['Pixel 7'] },
    },
  ],
});
