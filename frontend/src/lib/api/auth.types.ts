export type UserRole = 'admin' | 'sales' | 'accounting' | 'analyst' | 'director';

export type AuthUser = {
  id: string;
  email: string;
  role: UserRole;
  display_name: string;
  preferred_landing_route: string | null;
};

export type LoginCredentials = {
  email: string;
  password: string;
};

export type LoginResult = {
  access_token: string;
  token_type: 'bearer';
  expires_in: number;
  user: AuthUser;
};

export type RefreshResult = {
  access_token: string;
  token_type: 'bearer';
  expires_in: number;
};

export type LogoutResult = {
  ok: boolean;
};
