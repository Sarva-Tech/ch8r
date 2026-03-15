import { h } from 'preact';
import { useEffect } from 'preact/hooks';
import { isOpen, config, chatroomsHuman, chatroomsAI } from '../store/signals';
import { Launcher } from './Launcher';
import { ChatPanel } from './ChatPanel';
import { wsManagerBackground } from '../services/websocket';
import { sessionStore } from '../services/session';
import { createApiClient } from '../services/api';

interface AppProps {
  shadowHost: HTMLElement;
}

export function App({ shadowHost }: AppProps) {
  useEffect(() => {
    shadowHost.style.setProperty('--ch8r-accent', config.value?.accentColor ?? '#6366f1');
    shadowHost.style.setProperty('--ch8r-accent-fg', '#ffffff');

    const appUuid = config.value?.appUuid ?? '';
    const senderIdentifier = sessionStore.getSenderIdentifier(config.value?.userIdentifier, appUuid);
    const apiClient = createApiClient(
      config.value?.apiBaseUrl ?? window.location.origin,
      config.value?.token ?? '',
    );

    const fetchAll = () => {
      apiClient.loadChatrooms(appUuid, senderIdentifier, 'human').then(r => {
        if (r.ok) chatroomsHuman.value = r.data;
      });
      apiClient.loadChatrooms(appUuid, senderIdentifier, 'ai').then(r => {
        if (r.ok) chatroomsAI.value = r.data;
      });
    };

    fetchAll();

    // Update both signals when an unread_update arrives
    wsManagerBackground.onUnreadUpdate((event) => {
      chatroomsHuman.value = chatroomsHuman.value.map(c =>
        c.uuid === event.chatroom_uuid ? { ...c, has_unread: event.has_unread } : c
      );
      chatroomsAI.value = chatroomsAI.value.map(c =>
        c.uuid === event.chatroom_uuid ? { ...c, has_unread: event.has_unread } : c
      );
    });
    wsManagerBackground.onReconnect(fetchAll);
    wsManagerBackground.connect(senderIdentifier, () => {}, undefined, config.value?.apiBaseUrl);

    return () => { wsManagerBackground.disconnect(); };
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
