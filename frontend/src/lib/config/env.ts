const fallbackApiBaseUrl = 'http://localhost:8061/api/v1';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? fallbackApiBaseUrl;
export const ENABLE_LLM = String(import.meta.env.VITE_ENABLE_LLM ?? 'false').toLowerCase() === 'true';
export const DEFAULT_PRODUCT = String(import.meta.env.VITE_DEFAULT_PRODUCT ?? 'AI_95').toUpperCase();
