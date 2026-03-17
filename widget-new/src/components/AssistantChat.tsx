import { useEffect, useRef, useState } from 'preact/hooks';
import { sessionStore } from '../services/session';
import { createApiClient } from '../services/api';
import { wsManager } from '../services/websocket';
import { chatrooms, isTyping, sendError, wsStatus, config } from '../store/signals';
import type { ChatroomPreview, Message } from '../types/index';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { ChatroomList } from './ChatroomList';

export function AssistantChat() {
  const [activeChatroom, setActiveChatroom] = useState<ChatroomPreview | null>(null);
  const [listRefreshKey, setListRefreshKey] = useState(0);
  const [chatroomMode, setChatroomMode] = useState<'ai' | 'direct'>(config.value?.defaultMode ?? 'ai');
  const [chatroomName, setChatroomName] = useState<string>('');
  const messagesRef = useRef<Message[]>([]);
  const localMessages = useRef<Message[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const chatroomIdRef = useRef<string>('new_chat');

  useEffect(() => {
    return () => {
      wsManager.disconnect();
      isTyping.value = false;
      sendError.value = null;
    };
  }, []);

  // Connect WS and load messages when a chatroom is selected
  useEffect(() => {
    if (!activeChatroom) return;

    const appUuid = config.value?.appUuid ?? '';
    const senderIdentifier = sessionStore.getSenderIdentifier(config.value?.userIdentifier, appUuid);
    const isNew = activeChatroom.uuid === 'new_chat';

    chatroomIdRef.current = isNew ? 'new_chat' : activeChatroom.uuid;

    const onMessage = (msg: Message) => {
      // Only accept messages belonging to the active chatroom
      if (msg.chatroomIdentifier && chatroomIdRef.current !== 'new_chat' &&
          msg.chatroomIdentifier !== chatroomIdRef.current) return;
      isTyping.value = false;
      const updated = [...localMessages.current, msg];
      localMessages.current = updated;
      messagesRef.current = updated;
      setMessages(updated);
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
        localMessages.current = [greeting];
        messagesRef.current = [greeting];
        setMessages([greeting]);
      } else {
        localMessages.current = [];
        messagesRef.current = [];
        setMessages([]);
      }
      wsManager.connect(senderIdentifier, onMessage, () => { wsStatus.value = 'error'; }, config.value?.apiBaseUrl);
    } else {
      // Existing chatroom — fetch history from backend
      localMessages.current = [];
      messagesRef.current = [];
      setMessages([]);

      const apiClient = createApiClient(
        config.value?.apiBaseUrl ?? window.location.origin,
        config.value?.token ?? '',
      );

      apiClient.loadHistory(appUuid, activeChatroom.uuid, senderIdentifier).then(result => {
        if (result.ok) {
          localMessages.current = result.data;
          messagesRef.current = result.data;
          setMessages(result.data);
        } else {
          // Stale chatroom ID — reset to new_chat
          chatroomIdRef.current = 'new_chat';
          sessionStore.setChatroomId(appUuid, 'new_chat');
          localMessages.current = [];
          messagesRef.current = [];
          setMessages([]);
        }
      });

      wsManager.connect(senderIdentifier, onMessage, () => { wsStatus.value = 'error'; }, config.value?.apiBaseUrl);
    }

    // Set mode from chatroom data if available
    if (activeChatroom.mode) {
      setChatroomMode(activeChatroom.mode);
    }

    return () => { wsManager.disconnect(); };
  }, [activeChatroom]);

  const handleSelect = (chatroom: ChatroomPreview) => {
    // Optimistically clear unread for this chatroom
    chatrooms.value = chatrooms.value.map(c =>
      c.uuid === chatroom.uuid ? { ...c, has_unread: false } : c
    );
    setChatroomName(chatroom.name);
    setActiveChatroom(chatroom);
  };

  const handleBack = () => {
    wsManager.disconnect();
    localMessages.current = [];
    messagesRef.current = [];
    setMessages([]);
    chatroomIdRef.current = 'new_chat';
    isTyping.value = false;
    sendError.value = null;
    setChatroomName('');
    setChatroomMode('ai');
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
    const withUser = [...localMessages.current, userMsg];
    localMessages.current = withUser;
    messagesRef.current = withUser;
    setMessages(withUser);

    isTyping.value = true;
    sendError.value = null;

    const apiClient = createApiClient(
      config.value?.apiBaseUrl ?? window.location.origin,
      config.value?.token ?? '',
    );

    const defaultMode = config.value?.defaultMode ?? 'ai';

    const result = await apiClient.sendMessage(appUuid, {
      message,
      sender_identifier: senderIdentifier,
      chatroom_identifier: chatroomId,
      is_internal: false,
      mode: chatroomId === 'new_chat' ? chatroomMode : undefined,
    });

    if (result.ok) {
      const newChatroomId = String(result.data.chatroom_identifier);
      const wasNew = chatroomIdRef.current === 'new_chat';
      chatroomIdRef.current = newChatroomId;
      sessionStore.setChatroomId(appUuid, newChatroomId);

      // Update chatroomMode from server response
      if (result.data.mode === 'direct' || result.data.mode === 'ai') {
        setChatroomMode(result.data.mode);
      }

      if (wasNew) {
        setChatroomName(`Chat ${new Date().toLocaleDateString()}`);
      }

      // For direct mode, typing indicator should stop immediately (no AI response)
      if (result.data.mode === 'direct') {
        isTyping.value = false;
      }
    } else {
      sendError.value = result.error;
      isTyping.value = false;
    }
  };

  if (!activeChatroom) {
    return <ChatroomList onSelect={handleSelect} refreshKey={listRefreshKey} />;
  }

  const isNewChat = chatroomIdRef.current === 'new_chat';

  const handleModeToggle = async () => {
    const newMode = chatroomMode === 'ai' ? 'direct' : 'ai';
    if (isNewChat) {
      setChatroomMode(newMode);
      return;
    }
    const appUuid = config.value?.appUuid ?? '';
    const senderIdentifier = sessionStore.getSenderIdentifier(config.value?.userIdentifier, appUuid);
    const apiClient = createApiClient(
      config.value?.apiBaseUrl ?? window.location.origin,
      config.value?.token ?? '',
    );
    const result = await apiClient.updateChatroomMode(appUuid, chatroomIdRef.current, newMode, senderIdentifier);
    if (result.ok) {
      setChatroomMode(newMode);
    }
  };

  const modeToggle = (
    <button
      onClick={handleModeToggle}
      aria-label={`Switch to ${chatroomMode === 'ai' ? 'direct' : 'AI'} mode`}
      title={chatroomMode === 'ai' ? 'AI mode — click to switch to Direct' : 'Direct mode — click to switch to AI'}
      class={`text-xs px-2 py-0.5 rounded-full border transition-colors cursor-pointer ${
        chatroomMode === 'direct'
          ? 'text-blue-600 bg-blue-50 border-blue-200 hover:bg-blue-100'
          : 'text-purple-600 bg-purple-50 border-purple-200 hover:bg-purple-100'
      }`}
    >
      {chatroomMode === 'direct' ? 'Direct' : 'AI'}
    </button>
  );

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
        <span class="text-sm font-medium text-gray-700 truncate flex-1">
          {chatroomName || activeChatroom.name}
        </span>
        {modeToggle}
      </div>

      {sendError.value && (
        <div class="bg-red-50 px-4 py-2 text-sm text-red-700">
          Failed to send message. Please try again.
        </div>
      )}

      <MessageList messages={messages} isTyping={isTyping.value} />
      <MessageInput onSend={handleSend} disabled={false} />
    </div>
  );
}
