import { describe, expect, it } from 'vitest';
import { canAccessRole } from './access';

describe('canAccessRole', () => {
  it('allows access when no role restriction is provided', () => {
    expect(canAccessRole('admin')).toBe(true);
    expect(canAccessRole('analyst', [])).toBe(true);
  });

  it('enforces allowed roles', () => {
    expect(canAccessRole('admin', ['admin'])).toBe(true);
    expect(canAccessRole('analyst', ['admin'])).toBe(false);
  });
});
