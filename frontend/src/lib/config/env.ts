const fallbackApiBaseUrl = '/api/v1';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? fallbackApiBaseUrl;
export const ENABLE_LLM = String(import.meta.env.VITE_ENABLE_LLM ?? 'false').toLowerCase() === 'true';
export const ENABLE_DEMO_CREDENTIALS =
  String(import.meta.env.VITE_ENABLE_DEMO_CREDENTIALS ?? 'true').toLowerCase() === 'true';
export const DEFAULT_PRODUCT = String(import.meta.env.VITE_DEFAULT_PRODUCT ?? 'AI_95').toUpperCase();
export const DEFAULT_DATE_TO = String(import.meta.env.VITE_DEFAULT_DATE_TO ?? '').trim();
