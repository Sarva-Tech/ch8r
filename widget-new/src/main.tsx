import { h, render } from 'preact';
import { App } from './components/App';
import { config } from './store/signals';
import type { WidgetConfig, WidgetPosition, WidgetTheme, DarkModeConfig } from './types/index';
import widgetCss from './styles/widget.css?raw';
import { injectTheme, buildThemeCSS } from './themes/themeInjector';
import { createDarkModeDetector } from './themes/darkModeDetector';

const VALID_POSITIONS: WidgetPosition[] = ['bottom-right', 'bottom-left', 'top-right', 'top-left'];

export const VALID_THEMES: WidgetTheme[] = [
  'neutral', 'gray', 'blue', 'rose', 'orange', 'green', 'yellow', 'violet',
];

export function parsePosition(raw: string | null): WidgetPosition {
  return VALID_POSITIONS.includes(raw as WidgetPosition) ? (raw as WidgetPosition) : 'bottom-right';
}

export function parseOffset(raw: string | null): number {
  const n = parseInt(raw ?? '', 10);
  return Number.isFinite(n) && n >= 0 ? n : 16;
}

export function parseTheme(raw: string | null): WidgetTheme {
  if (VALID_THEMES.includes(raw as WidgetTheme)) {
    return raw as WidgetTheme;
  }
  if (raw !== null) {
    console.warn(`[Ch8rWidget] Unknown theme "${raw}", falling back to "neutral".`);
  }
  return 'neutral';
}

export function parseDarkMode(raw: string | null): DarkModeConfig {
  const VALID: DarkModeConfig[] = ['true', 'false', 'auto'];
  if (VALID.includes(raw as DarkModeConfig)) {
    return raw as DarkModeConfig;
  }
  if (raw !== null) {
    console.warn(`[Ch8rWidget] Unknown darkMode "${raw}", falling back to "auto".`);
  }
  return 'auto';
}

(function () {
  const currentScript = document.currentScript as HTMLScriptElement | null;

  let parsedConfig: WidgetConfig | null = null;
  let theme: WidgetTheme = 'neutral';
  let darkMode: DarkModeConfig = 'auto';

  if (window.Ch8rWidgetConfig) {
    parsedConfig = window.Ch8rWidgetConfig as WidgetConfig;
    theme = parseTheme(parsedConfig.theme ?? null);
    darkMode = parseDarkMode(parsedConfig.darkMode ?? null);
  } else if (currentScript) {
    const appUuid = currentScript.getAttribute('data-app-uuid') ?? undefined;
    const token = currentScript.getAttribute('data-token') ?? undefined;
    if (appUuid && token) {
      theme = parseTheme(currentScript.getAttribute('data-theme'));
      darkMode = parseDarkMode(currentScript.getAttribute('data-dark-mode'));
      parsedConfig = {
        appUuid,
        token,
        theme,
        darkMode,
        position: parsePosition(currentScript.getAttribute('data-position')),
        offsetTop: parseOffset(currentScript.getAttribute('data-offset-top')),
        offsetBottom: parseOffset(currentScript.getAttribute('data-offset-bottom')),
        offsetLeft: parseOffset(currentScript.getAttribute('data-offset-left')),
        offsetRight: parseOffset(currentScript.getAttribute('data-offset-right')),
        title: currentScript.getAttribute('data-title') ?? undefined,
        launcherIconUrl: currentScript.getAttribute('data-launcher-icon-url') ?? undefined,
        aiGreeting: currentScript.getAttribute('data-ai-greeting') ?? undefined,
        apiBaseUrl: currentScript.getAttribute('data-api-base-url') ?? undefined,
        userIdentifier: currentScript.getAttribute('data-user-identifier') ?? undefined,
        appName: currentScript.getAttribute('data-app-name') ?? undefined,
        appDescription: currentScript.getAttribute('data-app-description') ?? undefined,
        appLogoUrl: currentScript.getAttribute('data-app-logo-url') ?? undefined,
      };
    }
  }

  if (!parsedConfig?.appUuid || !parsedConfig?.token) {
    console.error('[Ch8rWidget] Missing required configuration: appUuid and token are required.');
    return;
  }

  config.value = parsedConfig;

  // Expose for live preview postMessage updates
  (window as any).__ch8rConfig = config;
  (window as any).__ch8rBuildThemeCSS = buildThemeCSS;

  const hostEl = document.createElement('div');
  hostEl.id = 'ch8r-widget-root';
  const shadow = hostEl.attachShadow({ mode: 'open' });

  const style = document.createElement('style');
  style.textContent = widgetCss;
  shadow.appendChild(style);

  const appRoot = document.createElement('div');
  shadow.appendChild(appRoot);

  injectTheme(shadow, theme);

  document.body.appendChild(hostEl);
  render(<App shadowHost={hostEl} />, appRoot);

  createDarkModeDetector(hostEl, darkMode);
})();
