import { h, render } from 'preact';
import { App } from './components/App';
import { config } from './store/signals';
import type { WidgetConfig } from './types/index';
import widgetCss from './styles/widget.css?raw';

(function () {
  // Read config from window global or script data attributes
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
        position: (currentScript.getAttribute('data-position') as WidgetConfig['position']) ?? undefined,
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

  // Set config signal
  config.value = parsedConfig;

  // Create host element and attach Shadow DOM
  const hostEl = document.createElement('div');
  hostEl.id = 'ch8r-widget-root';
  const shadow = hostEl.attachShadow({ mode: 'open' });

  // Inject styles
  const style = document.createElement('style');
  style.textContent = widgetCss;
  shadow.appendChild(style);

  // Create Preact render target
  const appRoot = document.createElement('div');
  shadow.appendChild(appRoot);

  // Apply theme CSS vars
  hostEl.style.setProperty('--ch8r-accent', parsedConfig.accentColor ?? '#6366f1');
  hostEl.style.setProperty('--ch8r-accent-fg', '#ffffff');

  // Append to body and render
  document.body.appendChild(hostEl);
  render(<App shadowHost={hostEl} />, appRoot);
})();
