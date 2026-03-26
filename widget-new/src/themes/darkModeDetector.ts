export type DarkModeConfig = 'auto' | 'true' | 'false';

export interface DarkModeDetector {
  destroy(): void;
}

const NO_OP_DETECTOR: DarkModeDetector = { destroy: () => {} };

function isDarkFromDOM(): boolean {
  return (
    document.documentElement.classList.contains('dark') ||
    document.body.classList.contains('dark')
  );
}

export function createDarkModeDetector(
  shadowHost: HTMLElement,
  darkMode: DarkModeConfig,
  onChange?: (isDark: boolean) => void,
): DarkModeDetector {
  if (darkMode === 'true') {
    shadowHost.classList.add('dark');
    return NO_OP_DETECTOR;
  }

  if (darkMode === 'false') {
    return NO_OP_DETECTOR;
  }

  // darkMode === 'auto'
  const mediaQuery =
    typeof window !== 'undefined' && typeof window.matchMedia !== 'undefined'
      ? window.matchMedia('(prefers-color-scheme: dark)')
      : null;

  // Determine initial state: DOM class takes priority over media query
  const getIsDark = (): boolean => {
    if (isDarkFromDOM()) return true;
    return mediaQuery ? mediaQuery.matches : false;
  };

  // Apply initial state
  const initialDark = getIsDark();
  if (initialDark) {
    shadowHost.classList.add('dark');
  } else {
    shadowHost.classList.remove('dark');
  }

  let observer: MutationObserver | null = null;
  let mediaListener: ((e: MediaQueryListEvent) => void) | null = null;

  const applyDark = (isDark: boolean) => {
    const wasDark = shadowHost.classList.contains('dark');
    if (isDark === wasDark) return;
    if (isDark) {
      shadowHost.classList.add('dark');
    } else {
      shadowHost.classList.remove('dark');
    }
    onChange?.(isDark);
  };

  // Attach MutationObserver on <html> and <body>
  if (typeof MutationObserver !== 'undefined') {
    observer = new MutationObserver(() => {
      applyDark(getIsDark());
    });
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class'],
    });
    observer.observe(document.body, {
      attributes: true,
      attributeFilter: ['class'],
    });
  }

  // Attach media query change listener
  if (mediaQuery) {
    mediaListener = (e: MediaQueryListEvent) => {
      // DOM class still takes priority
      if (!isDarkFromDOM()) {
        applyDark(e.matches);
      }
    };
    mediaQuery.addEventListener('change', mediaListener);
  }

  return {
    destroy() {
      if (observer) {
        observer.disconnect();
        observer = null;
      }
      if (mediaQuery && mediaListener) {
        mediaQuery.removeEventListener('change', mediaListener);
        mediaListener = null;
      }
    },
  };
}
