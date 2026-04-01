export type ApiErrorPayload = {
  code: string;
  message: string;
  details?: unknown;
};

export type ApiEnvelope<T> = {
  data: T;
  error: ApiErrorPayload | null;
  meta: Record<string, unknown>;
};

export class ApiHttpError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details?: unknown;

  constructor(params: { status: number; message: string; code?: string; details?: unknown }) {
    super(params.message);
    this.name = 'ApiHttpError';
    this.status = params.status;
    this.code = params.code ?? 'http_error';
    this.details = params.details;
  }
}

export async function parseApiEnvelope<T>(response: Response): Promise<T> {
  let payload: ApiEnvelope<T> | null = null;

  try {
    payload = (await response.json()) as ApiEnvelope<T>;
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const error = payload?.error;
    throw new ApiHttpError({
      status: response.status,
      code: error?.code,
      message: error?.message ?? `HTTP ${response.status}`,
      details: error?.details,
    });
  }

  if (!payload) {
    throw new ApiHttpError({
      status: response.status,
      message: 'Некорректный формат ответа API',
      code: 'http_error',
    });
  }

  if (payload.error) {
    throw new ApiHttpError({
      status: response.status,
      code: payload.error.code,
      message: payload.error.message,
      details: payload.error.details,
    });
  }

  return payload.data;
}
