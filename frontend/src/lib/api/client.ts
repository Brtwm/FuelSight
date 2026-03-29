import { API_BASE_URL } from '../config/env';

type ApiEnvelope<T> = {
  data: T;
  error: { code: string; message: string; details?: unknown } | null;
  meta: Record<string, unknown>;
};

type HealthData = {
  ok: boolean;
  app_env: string;
  version: string;
  timestamp: string;
};

export async function checkBackendHealth(): Promise<HealthData> {
  const response = await fetch(`${API_BASE_URL}/health`, {
    method: 'GET',
  });

  if (!response.ok) {
    throw new Error(`Backend health check failed: ${response.status}`);
  }

  const json = (await response.json()) as ApiEnvelope<HealthData>;

  if (json.error) {
    throw new Error(json.error.message);
  }

  return json.data;
}
