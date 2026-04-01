import { API_BASE_URL } from '../config/env';
import { parseApiEnvelope } from './http';

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

  return parseApiEnvelope<HealthData>(response);
}
