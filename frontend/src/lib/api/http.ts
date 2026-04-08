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

export type ApiResult<TData, TMeta extends Record<string, unknown>> = {
  data: TData;
  meta: TMeta;
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
  const result = await parseApiEnvelopeWithMeta<T, Record<string, unknown>>(response);
  return result.data;
}

export async function parseApiEnvelopeWithMeta<
  TData,
  TMeta extends Record<string, unknown>,
>(response: Response): Promise<ApiResult<TData, TMeta>> {
  let payload: ApiEnvelope<TData> | null = null;

  try {
    payload = (await response.json()) as ApiEnvelope<TData>;
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

  return {
    data: payload.data,
    meta: (payload.meta ?? {}) as TMeta,
  };
}
