import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';
import { parseTheme, parseDarkMode, VALID_THEMES } from './main';
import type { WidgetTheme } from './types';

describe('main — config parsing helpers', () => {
  describe('parseTheme', () => {
    it('returns the theme unchanged for each valid theme name', () => {
      for (const theme of VALID_THEMES) {
        expect(parseTheme(theme)).toBe(theme);
      }
    });

    it('returns "neutral" for null', () => {
      expect(parseTheme(null)).toBe('neutral');
    });

    it('returns "neutral" for an unknown string', () => {
      expect(parseTheme('unknown-theme')).toBe('neutral');
    });
  });

  describe('parseDarkMode', () => {
    it('returns "true" for "true"', () => {
      expect(parseDarkMode('true')).toBe('true');
    });

    it('returns "false" for "false"', () => {
      expect(parseDarkMode('false')).toBe('false');
    });

    it('returns "auto" for "auto"', () => {
      expect(parseDarkMode('auto')).toBe('auto');
    });

    it('returns "auto" for null', () => {
      expect(parseDarkMode(null)).toBe('auto');
    });

    it('returns "auto" for an unknown string', () => {
      expect(parseDarkMode('dark')).toBe('auto');
    });
  });

  // Feature: widget-theme-system, Property 7: Valid theme attribute parsing round-trip
  it('Property 7: valid theme attribute parsing round-trip', () => {
    fc.assert(
      fc.property(
        fc.constantFrom(...VALID_THEMES),
        (theme) => parseTheme(theme) === theme,
      ),
      { numRuns: 100 },
    );
  });

  // Feature: widget-theme-system, Property 8: Invalid theme/darkMode values fall back to defaults
  it('Property 8: invalid theme values fall back to "neutral"', () => {
    fc.assert(
      fc.property(
        fc.string().filter((s) => !VALID_THEMES.includes(s as WidgetTheme)),
        (invalid) => parseTheme(invalid) === 'neutral',
      ),
      { numRuns: 100 },
    );
  });

  it('Property 8: invalid darkMode values fall back to "auto"', () => {
    fc.assert(
      fc.property(
        fc.string().filter((s) => !['true', 'false', 'auto'].includes(s)),
        (invalid) => parseDarkMode(invalid) === 'auto',
      ),
      { numRuns: 100 },
    );
  });
});
