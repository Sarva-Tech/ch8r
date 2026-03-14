import { h } from 'preact';
import { useEffect } from 'preact/hooks';
import { isOpen, config } from '../store/signals';
import { Launcher } from './Launcher';
import { ChatPanel } from './ChatPanel';

interface AppProps {
  shadowHost: HTMLElement;
}

export function App({ shadowHost }: AppProps) {
  useEffect(() => {
    shadowHost.style.setProperty('--ch8r-accent', config.value?.accentColor ?? '#6366f1');
    shadowHost.style.setProperty('--ch8r-accent-fg', '#ffffff');
  }, []);

  return (
    <div>
      <Launcher
        isOpen={isOpen.value}
        position={config.value?.position}
        iconUrl={config.value?.launcherIconUrl}
        onOpen={() => { isOpen.value = true; }}
      />
      {isOpen.value && (
        <ChatPanel onClose={() => { isOpen.value = false; }} />
      )}
    </div>
  );
}
