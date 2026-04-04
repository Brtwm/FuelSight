import { describe, expect, it, vi } from 'vitest';
import { importInvalidationQueryKeys, invalidateImportCaches } from './invalidateImportCaches';

describe('invalidateImportCaches', () => {
  it('invalidates all expected query keys', async () => {
    const invalidateQueries = vi.fn().mockResolvedValue(undefined);
    const queryClient = { invalidateQueries } as never;

    await invalidateImportCaches(queryClient);

    expect(invalidateQueries).toHaveBeenCalledTimes(importInvalidationQueryKeys.length);
    for (const key of importInvalidationQueryKeys) {
      expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: [...key] });
    }
  });
});

