import { API_BASE_URL } from '../config/env';
import type { AuthUser, LoginCredentials, LoginResult, LogoutResult, RefreshResult } from './auth.types';
import { parseApiEnvelope } from './http';

type JsonRequestParams = {
  path: string;
  method: 'GET' | 'POST';
  accessToken?: string;
  body?: unknown;
};

async function jsonRequest<T>({ path, method, accessToken, body }: JsonRequestParams): Promise<T> {
  const headers = new Headers();
  if (body !== undefined) {
    headers.set('content-type', 'application/json');
  }
  if (accessToken) {
    headers.set('authorization', `Bearer ${accessToken}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    credentials: 'include',
  });

  return parseApiEnvelope<T>(response);
}

export async function loginWithPassword(payload: LoginCredentials): Promise<LoginResult> {
  return jsonRequest<LoginResult>({
    path: '/auth/login',
    method: 'POST',
    body: payload,
  });
}

export async function refreshAccessToken(): Promise<RefreshResult> {
  return jsonRequest<RefreshResult>({
    path: '/auth/refresh',
    method: 'POST',
  });
}

export async function fetchCurrentUser(accessToken: string): Promise<AuthUser> {
  return jsonRequest<AuthUser>({
    path: '/auth/me',
    method: 'GET',
    accessToken,
  });
}

export async function logoutSession(accessToken: string): Promise<LogoutResult> {
  return jsonRequest<LogoutResult>({
    path: '/auth/logout',
    method: 'POST',
    accessToken,
  });
}
