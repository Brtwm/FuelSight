import { API_BASE_URL } from '../config/env';
import { parseApiEnvelope } from './http';
import type { ExecutiveReportData, ExecutiveReportRequest } from './reports.types';

type AuthFetch = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

export async function generateExecutiveReport(
  authFetch: AuthFetch,
  payload: ExecutiveReportRequest = {},
): Promise<ExecutiveReportData> {
  const response = await authFetch(`${API_BASE_URL}/reports/executive`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return parseApiEnvelope<ExecutiveReportData>(response);
}
