import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import * as fc from 'fast-check';
import { createDarkModeDetector } from './darkModeDetector';

function createHost(): HTMLElement {
  const host = document.createElement('div');
  document.body.appendChild(host);
  return host;
}

function cleanup(host: HTMLElement) {
  host.remove();
  document.documentElement.classList.remove('dark');
  document.body.classList.remove('dark');
}

describe('darkModeDetector', () => {
  let host: HTMLElement;

  beforeEach(() => {
    // Ensure clean state
    document.documentElement.classList.remove('dark');
    document.body.classList.remove('dark');
    host = createHost();
  });

  afterEach(() => {
    cleanup(host);
  });

  it('darkMode="true" immediately adds .dark to host', () => {
    const detector = createDarkModeDetector(host, 'true');
    expect(host.classList.contains('dark')).toBe(true);
    detector.destroy();
  });

  it('darkMode="false" does not add .dark to host', () => {
    const detector = createDarkModeDetector(host, 'false');
    expect(host.classList.contains('dark')).toBe(false);
    detector.destroy();
  });

  it('darkMode="auto" with .dark on <html> adds .dark to host', () => {
    document.documentElement.classList.add('dark');
    const detector = createDarkModeDetector(host, 'auto');
    expect(host.classList.contains('dark')).toBe(true);
    detector.destroy();
  });

  it('darkMode="auto" with no dark signals does not add .dark to host', () => {
    const detector = createDarkModeDetector(host, 'auto');
    expect(host.classList.contains('dark')).toBe(false);
    detector.destroy();
  });

  it('destroy() called — subsequent DOM mutations do not affect host', async () => {
    const detector = createDarkModeDetector(host, 'auto');
    expect(host.classList.contains('dark')).toBe(false);

    detector.destroy();

    // Mutate DOM after destroy — should not affect host
    document.documentElement.classList.add('dark');
    await Promise.resolve();

    expect(host.classList.contains('dark')).toBe(false);
  });

  // Feature: widget-theme-system, Property 5: Dark class on html/body propagates to shadow host
  it('Property 5: dark class on html/body propagates to shadow host', () => {
    fc.assert(
      fc.property(
        fc.constantFrom('html', 'body'),
        fc.boolean(),
        (element, startDark) => {
          const testHost = createHost();
          const target =
            element === 'html' ? document.documentElement : document.body;

          // Set initial state
          if (startDark) {
            target.classList.add('dark');
          } else {
            target.classList.remove('dark');
          }

          const detector = createDarkModeDetector(testHost, 'auto');

          // At creation time, shadow host .dark should match the element's .dark
          const hostHasDark = testHost.classList.contains('dark');
          const elementHasDark = target.classList.contains('dark');
          const result = hostHasDark === elementHasDark;

          detector.destroy();
          cleanup(testHost);

          return result;
        },
      ),
      { numRuns: 100 },
    );
  });

  // Feature: widget-theme-system, Property 6: Detector cleanup prevents further updates
  it('Property 6: detector cleanup prevents further updates', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.boolean(),
        async (startDark) => {
          const testHost = createHost();

          // Set initial state
          if (startDark) {
            document.documentElement.classList.add('dark');
          } else {
            document.documentElement.classList.remove('dark');
            document.body.classList.remove('dark');
          }

          const detector = createDarkModeDetector(testHost, 'auto');
          const stateBeforeDestroy = testHost.classList.contains('dark');

          detector.destroy();

          // After destroy, toggle dark on both html and body
          if (stateBeforeDestroy) {
            document.documentElement.classList.remove('dark');
            document.body.classList.remove('dark');
          } else {
            document.documentElement.classList.add('dark');
            document.body.classList.add('dark');
          }

          await Promise.resolve();

          // Host should remain unchanged after destroy
          const result = testHost.classList.contains('dark') === stateBeforeDestroy;

          cleanup(testHost);
          return result;
        },
      ),
      { numRuns: 100 },
    );
  });
});
