import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import type { PropsWithChildren } from 'react';
import {
  fetchCurrentUser,
  loginWithPassword,
  logoutSession,
  refreshAccessToken,
} from '../../lib/api/auth';
import type { AuthUser, LoginCredentials } from '../../lib/api/auth.types';
import { requestWithRefresh } from './requestWithRefresh';

type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated';

type AuthContextValue = {
  status: AuthStatus;
  isAuthenticated: boolean;
  user: AuthUser | null;
  sessionExpired: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  authFetch: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;
  clearSessionExpired: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: PropsWithChildren) {
  const [status, setStatus] = useState<AuthStatus>('loading');
  const [user, setUser] = useState<AuthUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [sessionExpired, setSessionExpired] = useState(false);

  const accessTokenRef = useRef<string | null>(null);
  const refreshPromiseRef = useRef<Promise<string | null> | null>(null);

  useEffect(() => {
    accessTokenRef.current = accessToken;
  }, [accessToken]);

  const setAuthenticated = useCallback((nextAccessToken: string, nextUser: AuthUser) => {
    setAccessToken(nextAccessToken);
    setUser(nextUser);
    setStatus('authenticated');
    setSessionExpired(false);
  }, []);

  const clearSession = useCallback((markExpired: boolean) => {
    setAccessToken(null);
    setUser(null);
    setStatus('unauthenticated');
    if (markExpired) {
      setSessionExpired(true);
    }
  }, []);

  const refreshSession = useCallback(
    async (markExpired: boolean): Promise<string | null> => {
      if (refreshPromiseRef.current) {
        return refreshPromiseRef.current;
      }

      refreshPromiseRef.current = (async () => {
        try {
          const refreshResult = await refreshAccessToken();
          const profile = await fetchCurrentUser(refreshResult.access_token);
          setAuthenticated(refreshResult.access_token, profile);
          return refreshResult.access_token;
        } catch {
          clearSession(markExpired);
          return null;
        } finally {
          refreshPromiseRef.current = null;
        }
      })();

      return refreshPromiseRef.current;
    },
    [clearSession, setAuthenticated],
  );

  useEffect(() => {
    void (async () => {
      const token = await refreshSession(false);
      if (!token) {
        setStatus('unauthenticated');
      }
    })();
  }, [refreshSession]);

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      const loginResult = await loginWithPassword(credentials);
      setAuthenticated(loginResult.access_token, loginResult.user);
    },
    [setAuthenticated],
  );

  const logout = useCallback(async () => {
    const token = accessTokenRef.current;
    try {
      if (token) {
        await logoutSession(token);
      }
    } finally {
      clearSession(false);
    }
  }, [clearSession]);

  const authFetch = useCallback(
    async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      const response = await requestWithRefresh({
        input,
        init,
        accessToken: accessTokenRef.current,
        doFetch: (nextInput, nextInit) => fetch(nextInput, nextInit),
        refreshAccessToken: async () => refreshSession(true),
      });
      return response;
    },
    [refreshSession],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      isAuthenticated: status === 'authenticated' && user !== null && Boolean(accessToken),
      user,
      sessionExpired,
      login,
      logout,
      authFetch,
      clearSessionExpired: () => setSessionExpired(false),
    }),
    [accessToken, authFetch, login, logout, sessionExpired, status, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
