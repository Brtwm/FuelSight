import { createContext, useContext, useMemo, useState } from 'react';
import type { PropsWithChildren } from 'react';

export type UserRole = 'admin' | 'analyst';

type User = {
  email: string;
  role: UserRole;
};

type AuthContextValue = {
  isAuthenticated: boolean;
  user: User;
  login: (nextUser: User) => void;
  logout: () => void;
};

const STORAGE_KEY = 'fuelsight.auth.user';

function readStoredUser(): User | null {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as User;
    if (parsed.role === 'admin' || parsed.role === 'analyst') {
      return parsed;
    }
  } catch {
    return null;
  }

  return null;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<User>(() => readStoredUser() ?? { email: 'admin@fuelsight.local', role: 'admin' });
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => Boolean(readStoredUser()));

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated,
      user,
      login: (nextUser) => {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(nextUser));
        setUser(nextUser);
        setIsAuthenticated(true);
      },
      logout: () => {
        localStorage.removeItem(STORAGE_KEY);
        setIsAuthenticated(false);
      },
    }),
    [isAuthenticated, user],
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

