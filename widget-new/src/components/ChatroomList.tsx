import { useEffect, useState } from 'preact/hooks';
import { createApiClient } from '../services/api';
import { sessionStore } from '../services/session';
import { config, chatroomsHuman, chatroomsAI } from '../store/signals';
import { wsManager, wsManagerHuman, wsManagerBackground } from '../services/websocket';
import { UnreadBadge } from './UnreadBadge';
import type { ChatroomPreview } from '../types/index';
import { Signal } from '@preact/signals';

interface ChatroomListProps {
  onSelect: (chatroom: ChatroomPreview) => void;
  refreshKey?: number;
  type?: 'human' | 'ai';
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export function ChatroomList({ onSelect, refreshKey, type }: ChatroomListProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Use the correct signal based on type
  const signal: Signal<ChatroomPreview[]> = type === 'human' ? chatroomsHuman : chatroomsAI;

  const loadChatrooms = () => {
    setLoading(true);
    setError(null);
    const appUuid = config.value?.appUuid ?? '';
    const senderIdentifier = sessionStore.getSenderIdentifier(config.value?.userIdentifier, appUuid);
    const apiClient = createApiClient(
      config.value?.apiBaseUrl ?? window.location.origin,
      config.value?.token ?? '',
    );

    apiClient.loadChatrooms(appUuid, senderIdentifier, type).then(result => {
      if (result.ok) {
        signal.value = result.data;
      } else {
        setError(result.error);
      }
      setLoading(false);
    });
  };

  useEffect(() => {
    loadChatrooms();

    const handleUnreadUpdate = (event: { chatroom_uuid: string; has_unread: boolean }) => {
      signal.value = signal.value.map(c =>
        c.uuid === event.chatroom_uuid ? { ...c, has_unread: event.has_unread } : c
      );
    };

    wsManager.onUnreadUpdate(handleUnreadUpdate);
    wsManagerHuman.onUnreadUpdate(handleUnreadUpdate);
    wsManagerBackground.onUnreadUpdate(handleUnreadUpdate);
    wsManager.onReconnect(loadChatrooms);
    wsManagerHuman.onReconnect(loadChatrooms);
    wsManagerBackground.onReconnect(loadChatrooms);
  }, [refreshKey]);

  if (loading) {
    return (
      <div class="flex-1 flex items-center justify-center text-sm text-gray-400">
        Loading conversations…
      </div>
    );
  }

  if (error) {
    return (
      <div class="flex-1 flex items-center justify-center text-sm text-red-500 px-4 text-center">
        {error}
      </div>
    );
  }

  const rooms = signal.value;

  return (
    <div class="flex-1 overflow-y-auto flex flex-col">
      {/* New chat button */}
      <button
        onClick={() => onSelect({ uuid: 'new_chat', name: 'New conversation', last_message: null, has_unread: false })}
        class="flex items-center gap-3 px-4 py-3 border-b border-gray-100 hover:bg-gray-50 transition-colors text-left"
      >
        <span
          class="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 text-white text-lg"
          style={{ backgroundColor: 'var(--ch8r-accent)' }}
        >
          +
        </span>
        <span class="text-sm font-medium text-gray-700">New conversation</span>
      </button>

      {rooms.length === 0 && (
        <div class="flex-1 flex items-center justify-center text-sm text-gray-400 px-4 text-center">
          No conversations yet. Start one above.
        </div>
      )}

      {rooms.map(room => (
        <button
          key={room.uuid}
          onClick={() => {
            signal.value = signal.value.map(c =>
              c.uuid === room.uuid ? { ...c, has_unread: false } : c
            );
            onSelect(room);
          }}
          class="flex items-start gap-3 px-4 py-3 border-b border-gray-100 hover:bg-gray-50 transition-colors text-left w-full"
        >
          <span
            class="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 text-white text-sm font-semibold mt-0.5"
            style={{ backgroundColor: 'var(--ch8r-accent)' }}
          >
            {room.name.charAt(0).toUpperCase()}
          </span>
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between gap-2">
              <span class="text-sm font-medium text-gray-800 truncate">{room.name}</span>
              <div class="flex items-center gap-1.5 flex-shrink-0">
                {room.has_unread && <UnreadBadge />}
                {room.last_message && (
                  <span class="text-xs text-gray-400">
                    {timeAgo(room.last_message.created_at)}
                  </span>
                )}
              </div>
            </div>
            {room.last_message && (
              <p class="text-xs text-gray-500 truncate mt-0.5">{room.last_message.message}</p>
            )}
          </div>
        </button>
      ))}
    </div>
  );
}
