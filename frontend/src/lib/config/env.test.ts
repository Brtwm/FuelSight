import { describe, expect, it } from 'vitest';
import { API_BASE_URL } from './env';

describe('env config', () => {
  it('exports api base url', () => {
    expect(API_BASE_URL).toBeTypeOf('string');
    expect(API_BASE_URL.length).toBeGreaterThan(0);
  });
});
