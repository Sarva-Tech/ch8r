import { useEffect, useRef, useState } from 'preact/hooks';
import { sessionStore } from '../services/session';
import { createApiClient } from '../services/api';
import { wsManager } from '../services/websocket';
import { aiMessages, isTyping, sendError, wsStatus, config, isOpen, activeMode, unreadAI } from '../store/signals';
import type { ChatroomPreview, Message } from '../types/index';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { ChatroomList } from './ChatroomList';

export function AIAgentChat() {
  const [activeChatroom, setActiveChatroom] = useState<ChatroomPreview | null>(null);
  // Bump this to force ChatroomList to re-fetch (e.g. after a new chat is created)
  const [listRefreshKey, setListRefreshKey] = useState(0);
  const messagesRef = useRef<Message[]>([]);
  // Track the real chatroom ID separately — updating this does NOT re-trigger the WS effect
  const chatroomIdRef = useRef<string>('new_chat');
  // Track the display name separately so we can update it without re-connecting WS
  const [chatroomName, setChatroomName] = useState<string>('');

  useEffect(() => {
    return () => {
      wsManager.disconnect();
      isTyping.value = false;
      sendError.value = null;
    };
  }, []);

  // Connect WS and load messages only when a chatroom is selected
  useEffect(() => {
    if (!activeChatroom) return;

    const appUuid = config.value?.appUuid ?? '';
    const senderIdentifier = sessionStore.getSenderIdentifier(config.value?.userIdentifier, appUuid);
    const isNew = activeChatroom.uuid === 'new_chat';

    chatroomIdRef.current = isNew ? 'new_chat' : activeChatroom.uuid;

    const onMessage = (msg: Message) => {
      // Only accept messages belonging to the active AI chatroom
      if (msg.chatroomIdentifier && chatroomIdRef.current !== 'new_chat' &&
          msg.chatroomIdentifier !== chatroomIdRef.current) return;
      isTyping.value = false;
      const updated = [...messagesRef.current, msg];
      messagesRef.current = updated;
      aiMessages.value = updated;
      // Increment unread if widget is closed or user is on a different mode
      if (!isOpen.value || activeMode.value !== 'ai') {
        unreadAI.value += 1;
      }
    };

    if (isNew) {
      // Fresh chat — show greeting if configured
      if (config.value?.aiGreeting) {
        const greeting: Message = {
          uuid: crypto.randomUUID(),
          message: config.value.aiGreeting,
          senderIdentifier: 'agent',
          chatroomIdentifier: 'new_chat',
          createdAt: new Date().toISOString(),
          isOwn: false,
        };
        aiMessages.value = [greeting];
        messagesRef.current = [greeting];
      } else {
        aiMessages.value = [];
        messagesRef.current = [];
      }
      wsManager.connect(senderIdentifier, onMessage, () => { wsStatus.value = 'error'; }, config.value?.apiBaseUrl);
    } else {
      // Existing chatroom — fetch history from backend
      aiMessages.value = [];
      messagesRef.current = [];
      const apiClient = createApiClient(
        config.value?.apiBaseUrl ?? window.location.origin,
        config.value?.token ?? '',
      );
      apiClient.loadHistory(appUuid, activeChatroom.uuid, senderIdentifier).then(result => {
        if (result.ok) {
          aiMessages.value = result.data;
          messagesRef.current = result.data;
        }
      });
      wsManager.connect(senderIdentifier, onMessage, () => { wsStatus.value = 'error'; }, config.value?.apiBaseUrl);
    }

    return () => { wsManager.disconnect(); };
  }, [activeChatroom]);

  const handleSelect = (chatroom: ChatroomPreview) => {
    unreadAI.value = 0;
    setChatroomName(chatroom.name);
    setActiveChatroom(chatroom);
  };

  const handleBack = () => {
    wsManager.disconnect();
    aiMessages.value = [];
    messagesRef.current = [];
    chatroomIdRef.current = 'new_chat';
    isTyping.value = false;
    sendError.value = null;
    setChatroomName('');
    // Always bump so ChatroomList re-fetches fresh data when we return
    setListRefreshKey(k => k + 1);
    setActiveChatroom(null);
  };

  const handleSend = async (message: string) => {
    const appUuid = config.value?.appUuid ?? '';
    const senderIdentifier = sessionStore.getSenderIdentifier(config.value?.userIdentifier, appUuid);
    const chatroomId = chatroomIdRef.current;

    const userMsg: Message = {
      uuid: crypto.randomUUID(),
      message,
      senderIdentifier,
      chatroomIdentifier: chatroomId,
      createdAt: new Date().toISOString(),
      isOwn: true,
    };
    const withUser = [...messagesRef.current, userMsg];
    messagesRef.current = withUser;
    aiMessages.value = withUser;

    isTyping.value = true;
    sendError.value = null;

    const apiClient = createApiClient(
      config.value?.apiBaseUrl ?? window.location.origin,
      config.value?.token ?? '',
    );

    const result = await apiClient.sendMessage(appUuid, {
      message,
      sender_identifier: senderIdentifier,
      chatroom_identifier: chatroomId,
      send_to_participant: false,
    });

    if (result.ok) {
      const newChatroomId = String(result.data.chatroom_identifier);
      const wasNew = chatroomIdRef.current === 'new_chat';
      chatroomIdRef.current = newChatroomId;
      sessionStore.setChatroomId(appUuid, newChatroomId, 'ai');
      if (wasNew) {
        setChatroomName(`Chat ${new Date().toLocaleDateString()}`);
      }
    } else {
      sendError.value = result.error;
      isTyping.value = false;
    }
  };

  if (!activeChatroom) {
    return <ChatroomList onSelect={handleSelect} refreshKey={listRefreshKey} type="ai" />;
  }

  return (
    <div class="flex flex-col h-full">
      <div class="flex items-center gap-2 px-3 py-2 border-b border-gray-100 bg-gray-50">
        <button
          onClick={handleBack}
          aria-label="Back to conversations"
          class="p-1 rounded hover:bg-gray-200 transition-colors text-gray-600"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-5 h-5">
            <path fill-rule="evenodd" d="M17 10a.75.75 0 0 1-.75.75H5.612l4.158 3.96a.75.75 0 1 1-1.04 1.08l-5.5-5.25a.75.75 0 0 1 0-1.08l5.5-5.25a.75.75 0 1 1 1.04 1.08L5.612 9.25H16.25A.75.75 0 0 1 17 10Z" clip-rule="evenodd" />
          </svg>
        </button>
        <span class="text-sm font-medium text-gray-700 truncate">
          {chatroomName || activeChatroom.name}
        </span>
      </div>

      {sendError.value && (
        <div class="bg-red-50 px-4 py-2 text-sm text-red-700">
          AI is temporarily unavailable. Please try again.
        </div>
      )}

      <MessageList messages={aiMessages.value} isTyping={isTyping.value} />
      <MessageInput onSend={handleSend} disabled={isTyping.value} />
    </div>
  );
}
