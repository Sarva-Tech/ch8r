import { h, render } from 'preact';
import { App } from './components/App';
import { config } from './store/signals';
import type { WidgetConfig, WidgetPosition } from './types/index';
import widgetCss from './styles/widget.css?raw';

const VALID_POSITIONS: WidgetPosition[] = ['bottom-right', 'bottom-left', 'top-right', 'top-left'];

export function parsePosition(raw: string | null): WidgetPosition {
  return VALID_POSITIONS.includes(raw as WidgetPosition) ? (raw as WidgetPosition) : 'bottom-right';
}

export function parseOffset(raw: string | null): number {
  const n = parseInt(raw ?? '', 10);
  return Number.isFinite(n) && n >= 0 ? n : 16;
}

(function () {
  const currentScript = document.currentScript as HTMLScriptElement | null;

  let parsedConfig: WidgetConfig | null = null;

  if (window.Ch8rWidgetConfig) {
    parsedConfig = window.Ch8rWidgetConfig as WidgetConfig;
  } else if (currentScript) {
    const appUuid = currentScript.getAttribute('data-app-uuid') ?? undefined;
    const token = currentScript.getAttribute('data-token') ?? undefined;
    if (appUuid && token) {
      parsedConfig = {
        appUuid,
        token,
        accentColor: currentScript.getAttribute('data-accent-color') ?? undefined,
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

  const hostEl = document.createElement('div');
  hostEl.id = 'ch8r-widget-root';
  const shadow = hostEl.attachShadow({ mode: 'open' });

  const style = document.createElement('style');
  style.textContent = widgetCss;
  shadow.appendChild(style);

  const appRoot = document.createElement('div');
  shadow.appendChild(appRoot);

  hostEl.style.setProperty('--ch8r-accent', parsedConfig.accentColor ?? '#6366f1');
  hostEl.style.setProperty('--ch8r-accent-fg', '#ffffff');

  document.body.appendChild(hostEl);
  render(<App shadowHost={hostEl} />, appRoot);
})();
