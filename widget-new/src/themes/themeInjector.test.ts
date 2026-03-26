import { describe, it, expect, beforeEach } from 'vitest';
import * as fc from 'fast-check';
import { buildThemeCSS, injectTheme } from './themeInjector';
import type { WidgetTheme } from '../types';

const ALL_THEMES: WidgetTheme[] = [
  'neutral', 'gray', 'blue', 'rose', 'orange', 'green', 'yellow', 'violet',
];

const REQUIRED_TOKENS = [
  '--background',
  '--foreground',
  '--card',
  '--card-foreground',
  '--primary',
  '--primary-foreground',
  '--secondary',
  '--secondary-foreground',
  '--muted',
  '--muted-foreground',
  '--accent',
  '--accent-foreground',
  '--destructive',
  '--border',
  '--input',
  '--ring',
  '--radius',
];

function createShadowRoot(): ShadowRoot {
  const host = document.createElement('div');
  document.body.appendChild(host);
  return host.attachShadow({ mode: 'open' });
}

describe('themeInjector', () => {
  describe('injectTheme', () => {
    it('creates a <style id="ch8r-theme"> element in the shadow root', () => {
      const shadowRoot = createShadowRoot();
      injectTheme(shadowRoot, 'neutral');
      const styleEl = shadowRoot.getElementById('ch8r-theme');
      expect(styleEl).not.toBeNull();
      expect(styleEl?.tagName.toLowerCase()).toBe('style');
    });

    it('does not create duplicate elements when called twice', () => {
      const shadowRoot = createShadowRoot();
      injectTheme(shadowRoot, 'neutral');
      injectTheme(shadowRoot, 'blue');
      const styleEls = shadowRoot.querySelectorAll('#ch8r-theme');
      expect(styleEls.length).toBe(1);
    });
  });

  // Feature: widget-theme-system, Property 1: All semantic tokens present in generated CSS
  it('Property 1: all semantic tokens present in generated CSS', () => {
    fc.assert(
      fc.property(
        fc.constantFrom(...ALL_THEMES),
        (theme) => {
          const css = buildThemeCSS(theme);
          return REQUIRED_TOKENS.every((token) => css.includes(token));
        },
      ),
      { numRuns: 100 },
    );
  });

  // Feature: widget-theme-system, Property 2: Dark variant block present in generated CSS
  it('Property 2: dark variant block present in generated CSS', () => {
    fc.assert(
      fc.property(
        fc.constantFrom(...ALL_THEMES),
        (theme) => {
          const css = buildThemeCSS(theme);
          return css.includes(':host(.dark)') && css.includes('--background');
        },
      ),
      { numRuns: 100 },
    );
  });

  // Feature: widget-theme-system, Property 4: Theme injection is idempotent and updates in place
  it('Property 4: theme injection is idempotent and updates in place', () => {
    fc.assert(
      fc.property(
        fc.constantFrom(...ALL_THEMES),
        fc.constantFrom(...ALL_THEMES),
        (themeA, themeB) => {
          const shadowRoot = createShadowRoot();
          injectTheme(shadowRoot, themeA);
          injectTheme(shadowRoot, themeB);
          const styleEls = shadowRoot.querySelectorAll('#ch8r-theme');
          return (
            styleEls.length === 1 &&
            styleEls[0].textContent === buildThemeCSS(themeB)
          );
        },
      ),
      { numRuns: 100 },
    );
  });
});
