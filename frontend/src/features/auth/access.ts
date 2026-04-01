import type { UserRole } from '../../lib/api/auth.types';

export function canAccessRole(role: UserRole, allowedRoles?: UserRole[]): boolean {
  if (!allowedRoles || allowedRoles.length === 0) {
    return true;
  }
  return allowedRoles.includes(role);
}
