import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';
import { THEMES, type TokenMap } from './themes';
import type { WidgetTheme } from '../types';

const ALL_THEMES: WidgetTheme[] = [
  'neutral', 'gray', 'blue', 'rose', 'orange', 'green', 'yellow', 'violet',
];

const REQUIRED_KEYS: (keyof TokenMap)[] = [
  'background',
  'foreground',
  'card',
  'card-foreground',
  'primary',
  'primary-foreground',
  'secondary',
  'secondary-foreground',
  'muted',
  'muted-foreground',
  'accent',
  'accent-foreground',
  'destructive',
  'border',
  'input',
  'ring',
  'radius',
];

describe('THEMES', () => {
  it('has exactly 8 theme entries', () => {
    expect(Object.keys(THEMES)).toHaveLength(8);
    expect(Object.keys(THEMES).sort()).toEqual(ALL_THEMES.slice().sort());
  });

  it('neutral light values match main.css :root block', () => {
    const { light } = THEMES.neutral;
    expect(light.background).toBe('oklch(1 0 0)');
    expect(light.foreground).toBe('oklch(0.145 0 0)');
    expect(light.primary).toBe('oklch(0.205 0 0)');
    expect(light['primary-foreground']).toBe('oklch(0.985 0 0)');
    expect(light.destructive).toBe('oklch(0.577 0.245 27.325)');
    expect(light.border).toBe('oklch(0.922 0 0)');
    expect(light.ring).toBe('oklch(0.708 0 0)');
    expect(light.radius).toBe('0.625rem');
  });

  it('neutral dark values match main.css .dark block', () => {
    const { dark } = THEMES.neutral;
    expect(dark.background).toBe('oklch(0.145 0 0)');
    expect(dark.foreground).toBe('oklch(0.985 0 0)');
    expect(dark.primary).toBe('oklch(0.922 0 0)');
    expect(dark.border).toBe('oklch(1 0 0 / 10%)');
    expect(dark.input).toBe('oklch(1 0 0 / 15%)');
  });

  // Feature: widget-theme-system, Property 3: Every theme has both light and dark token maps
  it('Property 3: every theme has both light and dark token maps with all required keys', () => {
    fc.assert(
      fc.property(
        fc.constantFrom(...ALL_THEMES),
        (theme) => {
          const entry = THEMES[theme];
          return REQUIRED_KEYS.every(
            (k) =>
              typeof entry.light[k] === 'string' &&
              entry.light[k].length > 0 &&
              typeof entry.dark[k] === 'string' &&
              entry.dark[k].length > 0,
          );
        },
      ),
      { numRuns: 100 },
    );
  });
});
