import type { ExternalContextQuality } from '../../lib/api/common.types';

export function isVerifiedLocalExternalContext(
  context: ExternalContextQuality | null | undefined,
): boolean {
  return context?.provider_mode === 'manual_snapshot'
    && typeof context.coverage_ratio === 'number'
    && context.coverage_ratio >= 0.95;
}
