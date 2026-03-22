/// <reference types="vite/client" />

import type { WidgetConfig } from './types/index';

declare global {
  interface Window {
    Ch8rWidgetConfig?: WidgetConfig;
  }
}
