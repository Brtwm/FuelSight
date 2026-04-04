import type { QueryClient } from '@tanstack/react-query';

export const importInvalidationQueryKeys = [
  ['kpi'],
  ['dashboard'],
  ['analytics'],
  ['forecast'],
  ['backtests'],
] as const;

export async function invalidateImportCaches(queryClient: QueryClient): Promise<void> {
  await Promise.all(
    importInvalidationQueryKeys.map((queryKey) =>
      queryClient.invalidateQueries({
        queryKey: [...queryKey],
      }),
    ),
  );
}

