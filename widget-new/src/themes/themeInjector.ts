import { THEMES } from './themes';
import type { WidgetTheme } from '../types';
import type { TokenMap } from './themes';

const TOKEN_KEYS: (keyof TokenMap)[] = [
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
  'header-bg',
  'header-fg',
];

function buildTokenBlock(tokens: TokenMap): string {
  return TOKEN_KEYS.map((key) => `  --${key}: ${tokens[key]};`).join('\n');
}

export function buildThemeCSS(theme: WidgetTheme): string {
  const { light, dark } = THEMES[theme];
  return `:host {\n${buildTokenBlock(light)}\n}\n:host(.dark) {\n${buildTokenBlock(dark)}\n}`;
}

export function injectTheme(shadowRoot: ShadowRoot, theme: WidgetTheme): void {
  let styleEl = shadowRoot.getElementById('ch8r-theme') as HTMLStyleElement | null;
  if (!styleEl) {
    styleEl = document.createElement('style');
    styleEl.id = 'ch8r-theme';
    shadowRoot.appendChild(styleEl);
  }
  styleEl.textContent = buildThemeCSS(theme);
}
