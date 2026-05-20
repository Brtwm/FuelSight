import { ApiHttpError } from './http';

export function getSectionErrorMessage(
  errors: unknown[],
  fallbackMessage: string,
): string {
  return errors.some((error) => error instanceof ApiHttpError && error.status === 403)
    ? 'У вашей роли нет доступа к этому разделу'
    : fallbackMessage;
}
