import { describe, expect, it } from 'vitest';
import { API_BASE_URL, DEFAULT_DATE_TO, DEFAULT_PRODUCT } from './env';

describe('env config', () => {
  it('exports api base url', () => {
    expect(API_BASE_URL).toBeTypeOf('string');
    expect(API_BASE_URL.length).toBeGreaterThan(0);
  });

  it('exports default product', () => {
    expect(DEFAULT_PRODUCT).toBeTypeOf('string');
    expect(DEFAULT_PRODUCT.length).toBeGreaterThan(0);
  });

  it('exports optional default date', () => {
    expect(DEFAULT_DATE_TO).toBeTypeOf('string');
  });
});
