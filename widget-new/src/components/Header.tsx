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
      style={{ backgroundColor: 'var(--ch8r-accent)', color: 'var(--ch8r-accent-fg)' }}
    >
      <div class="flex items-center gap-3 min-w-0">
        {appLogoUrl && (
          <img
            src={appLogoUrl}
            width="32"
            height="32"
            style={{ objectFit: 'contain', flexShrink: 0 }}
            alt=""
            onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }}
          />
        )}
        <div class="min-w-0">
          <p class="font-semibold text-sm truncate">{appName ?? 'Ch8r'}</p>
          <p class="text-xs opacity-80 truncate">
            {appDescription ?? (
              <span>
                Powered by{' '}
                <a
                  href="https://ch8r.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: 'inherit', opacity: 0.9 }}
                >
                  Ch8r
                </a>
              </span>
            )}
          </p>
        </div>
      </div>
      <button
        onClick={onClose}
        aria-label="Close chat"
        class="flex-shrink-0 ml-2 p-1 rounded hover:opacity-70 transition-opacity text-lg leading-none"
        style={{ color: 'var(--ch8r-accent-fg)' }}
      >
        ×
      </button>
    </div>
  );
}
