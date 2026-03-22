import { h } from 'preact';
import type { WidgetConfig } from '../types/index';

export interface PositionStyles {
  launcher: h.JSX.CSSProperties;
  panel: h.JSX.CSSProperties;
}

const LAUNCHER_SIZE_PX = 56;
const PANEL_GAP_PX = 8;

export function computePositionStyles(config: Partial<WidgetConfig>): PositionStyles {
  const position = config.position ?? 'bottom-right';

  const isTop = position.startsWith('top-');
  const isLeft = position.endsWith('-left');

  const verticalAxis = isTop ? 'top' : 'bottom';
  const horizontalAxis = isLeft ? 'left' : 'right';

  const verticalOffset = isTop
    ? (config.offsetTop ?? 16)
    : (config.offsetBottom ?? 16);

  const horizontalOffset = isLeft
    ? (config.offsetLeft ?? 16)
    : (config.offsetRight ?? 16);

  const panelVerticalOffset = LAUNCHER_SIZE_PX + PANEL_GAP_PX + verticalOffset;

  const launcher: h.JSX.CSSProperties = {
    position: 'fixed',
    [verticalAxis]: `${verticalOffset}px`,
    [horizontalAxis]: `${horizontalOffset}px`,
    zIndex: 9999,
  };

  const panel: h.JSX.CSSProperties = {
    position: 'fixed',
    [verticalAxis]: `${panelVerticalOffset}px`,
    [horizontalAxis]: `${horizontalOffset}px`,
    zIndex: 9998,
  };

  return { launcher, panel };
}
