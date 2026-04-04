import { API_BASE_URL } from '../config/env';
import { parseApiEnvelope } from './http';
import type { GenerateHistoryPayload, ImportJob, ImportJobDetails, ImportUploadResult } from './import.types';

type AuthFetch = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

async function uploadFile(
  path: string,
  file: File,
  authFetch: AuthFetch,
  sourceName?: string,
): Promise<ImportUploadResult> {
  const formData = new FormData();
  formData.append('file', file);
  if (sourceName && sourceName.trim()) {
    formData.append('source_name', sourceName.trim());
  }

  const response = await authFetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    body: formData,
  });
  return parseApiEnvelope<ImportUploadResult>(response);
}

export async function uploadSalesFile(
  file: File,
  authFetch: AuthFetch,
  sourceName?: string,
): Promise<ImportUploadResult> {
  return uploadFile('/import/sales', file, authFetch, sourceName);
}

export async function uploadPurchasesFile(
  file: File,
  authFetch: AuthFetch,
  sourceName?: string,
): Promise<ImportUploadResult> {
  return uploadFile('/import/purchases', file, authFetch, sourceName);
}

export async function generateHistoryData(
  payload: GenerateHistoryPayload,
  authFetch: AuthFetch,
): Promise<ImportUploadResult> {
  const response = await authFetch(`${API_BASE_URL}/import/generate-demo`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  return parseApiEnvelope<ImportUploadResult>(response);
}

export async function fetchImportJobs(
  authFetch: AuthFetch,
  params?: { entity_type?: string; status?: string; limit?: number },
): Promise<ImportJob[]> {
  const search = new URLSearchParams();
  if (params?.entity_type) {
    search.set('entity_type', params.entity_type);
  }
  if (params?.status) {
    search.set('status', params.status);
  }
  if (params?.limit) {
    search.set('limit', String(params.limit));
  }
  const suffix = search.size > 0 ? `?${search.toString()}` : '';
  const response = await authFetch(`${API_BASE_URL}/import/jobs${suffix}`, {
    method: 'GET',
  });
  return parseApiEnvelope<ImportJob[]>(response);
}

export async function fetchImportJobById(jobId: string, authFetch: AuthFetch): Promise<ImportJobDetails> {
  const response = await authFetch(`${API_BASE_URL}/import/jobs/${jobId}`, {
    method: 'GET',
  });
  return parseApiEnvelope<ImportJobDetails>(response);
}

