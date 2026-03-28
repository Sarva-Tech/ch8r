import { h } from 'preact';

interface HeaderProps {
  appName?: string;
  appDescription?: string;
  appLogoUrl?: string;
  onClose: () => void;
}

export function Header({ appName, appDescription, appLogoUrl, onClose }: HeaderProps) {
  return (
    <div
      class="flex items-center justify-between px-4 py-3"
      style={{ background: 'var(--header-bg)', color: 'var(--header-fg)' }}
    >
      <div class="flex items-center gap-3 min-w-0">
        {appLogoUrl ? (
          <img
            src={appLogoUrl}
            width="32"
            height="32"
            class="rounded-full flex-shrink-0 bg-primary-foreground/20"
            style={{ objectFit: 'contain' }}
            alt=""
            onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }}
          />
        ) : (
          <div class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: 'color-mix(in srgb, var(--header-fg) 15%, transparent)' }}>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4" aria-hidden="true">
              <path d="M4.913 2.658c2.075-.27 4.19-.408 6.337-.408 2.147 0 4.262.139 6.337.408 1.922.25 3.291 1.861 3.405 3.727a4.403 4.403 0 0 0-1.032-.211 50.89 50.89 0 0 0-8.42 0c-2.358.196-4.04 2.19-4.04 4.434v4.286a4.47 4.47 0 0 0 2.433 3.984L7.28 21.53A.75.75 0 0 1 6 21v-4.03a48.527 48.527 0 0 1-1.087-.128C2.905 16.58 1.5 14.833 1.5 12.862V6.638c0-1.97 1.405-3.718 3.413-3.979Z" />
              <path d="M15.75 7.5c-1.376 0-2.739.057-4.086.169C10.124 7.797 9 9.103 9 10.609v4.285c0 1.507 1.128 2.814 2.67 2.94 1.243.102 2.5.157 3.768.165l2.782 2.781a.75.75 0 0 0 1.28-.53v-2.39l.33-.026c1.542-.125 2.67-1.433 2.67-2.94v-4.286c0-1.505-1.125-2.811-2.664-2.94A49.392 49.392 0 0 0 15.75 7.5Z" />
            </svg>
          </div>
        )}
        <div class="min-w-0 leading-tight">
          <div class="font-semibold text-sm truncate">{appName ?? 'Ch8r'}</div>
          <div class="text-xs truncate" style={{ opacity: 0.75 }}>
            {appDescription ?? (
              <span>
                Powered by{' '}
                <a
                  href="https://ch8r.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: 'inherit', textDecoration: 'underline' }}
                >
                  ch8r
                </a>
              </span>
            )}
          </div>
        </div>
      </div>
      <button
        onClick={onClose}
        aria-label="Close chat"
        class="flex-shrink-0 ml-2 p-1.5 rounded-lg transition-colors"
        style={{ background: 'color-mix(in srgb, var(--header-fg) 15%, transparent)' }}
        onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = 'color-mix(in srgb, var(--header-fg) 25%, transparent)'; }}
        onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = 'color-mix(in srgb, var(--header-fg) 15%, transparent)'; }}
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4" aria-hidden="true">
          <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
        </svg>
      </button>
    </div>
  );
}
