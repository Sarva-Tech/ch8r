import { useEffect, useRef, useState } from 'preact/hooks';
import { wsManagerHuman } from '../services/websocket';
import { sessionStore } from '../services/session';
import { createApiClient } from '../services/api';
import { humanMessages, wsStatus, sendError, agentInfo, config, isOpen, activeMode, unreadHuman } from '../store/signals';
import type { AgentInfo, Message } from '../types/index';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';

// Agent list view — shows the app owner as the only agent
function AgentList({ agent, onSelect }: { agent: AgentInfo | null; onSelect: () => void }) {
  if (!agent) {
    return (
      <div class="flex-1 flex items-center justify-center text-sm text-gray-400">
        Loading agents…
      </div>
    );
  }
  return (
    <div class="flex-1 overflow-y-auto flex flex-col">
      <button
        onClick={onSelect}
        class="flex items-center gap-3 px-4 py-4 border-b border-gray-100 hover:bg-gray-50 transition-colors text-left w-full"
      >
        <div class="relative flex-shrink-0">
          <div
            class="w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-semibold"
            style={{ backgroundColor: 'var(--ch8r-accent)' }}
          >
            {agent.name.charAt(0).toUpperCase()}
          </div>
          <span
            class={`absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 border-white ${agent.isOnline ? 'bg-green-400' : 'bg-gray-300'}`}
          />
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-gray-800">{agent.name}</p>
          <p class="text-xs text-gray-500">{agent.role}</p>
        </div>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4 text-gray-400 flex-shrink-0">
          <path fill-rule="evenodd" d="M8.22 5.22a.75.75 0 0 1 1.06 0l4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.75.75 0 0 1-1.06-1.06L11.94 10 8.22 6.28a.75.75 0 0 1 0-1.06Z" clip-rule="evenodd" />
        </svg>
      </button>
    </div>
  );
}

export function HumanAgentChat() {
  const [activeAgent, setActiveAgent] = useState<AgentInfo | null>(null);
  const messagesRef = useRef<Message[]>([]);
  const chatroomIdRef = useRef<string>('new_chat');

  // Fetch agent info on mount
  useEffect(() => {
    const appUuid = config.value?.appUuid ?? '';
    const apiClient = createApiClient(
      config.value?.apiBaseUrl ?? window.location.origin,
      config.value?.token ?? '',
    );
    apiClient.loadHumanAgent(appUuid).then(result => {
      if (result.ok) agentInfo.value = result.data;
    });
    return () => {
      wsManagerHuman.disconnect();
      sendError.value = null;
    };
  }, []);

  // Connect WS + load history when agent is selected
  useEffect(() => {
    if (!activeAgent) return;

    const appUuid = config.value?.appUuid ?? '';
    const senderIdentifier = sessionStore.getSenderIdentifier(config.value?.userIdentifier, appUuid);

    // Restore existing chatroom for this agent conversation (scoped to 'human' mode)
    const savedId = sessionStore.getChatroomId(appUuid, 'human');
    chatroomIdRef.current = savedId ?? 'new_chat';

    humanMessages.value = [];
    messagesRef.current = [];

    const apiClient = createApiClient(
      config.value?.apiBaseUrl ?? window.location.origin,
      config.value?.token ?? '',
    );

    // Load history if we have an existing chatroom
    if (chatroomIdRef.current !== 'new_chat') {
      apiClient.loadHistory(appUuid, chatroomIdRef.current, senderIdentifier).then(result => {
        if (result.ok) {
          humanMessages.value = result.data;
          messagesRef.current = result.data;
        }
      });
    }

    const onMessage = (msg: Message) => {
      // Only accept messages belonging to the active human agent chatroom
      if (msg.chatroomIdentifier && chatroomIdRef.current !== 'new_chat' &&
          msg.chatroomIdentifier !== chatroomIdRef.current) return;
      const updated = [...messagesRef.current, msg];
      messagesRef.current = updated;
      humanMessages.value = updated;
      // Increment unread if widget is closed or user is on a different mode
      if (!isOpen.value || activeMode.value !== 'human') {
        unreadHuman.value += 1;
      }
    };

    wsManagerHuman.connect(senderIdentifier, onMessage, () => {
      wsStatus.value = 'error';
    }, config.value?.apiBaseUrl);

    return () => { wsManagerHuman.disconnect(); };
  }, [activeAgent]);

  const handleSelectAgent = () => {
    unreadHuman.value = 0;
    setActiveAgent(agentInfo.value);
  };

  const handleBack = () => {
    wsManagerHuman.disconnect();
    humanMessages.value = [];
    messagesRef.current = [];
    sendError.value = null;
    setActiveAgent(null);
  };

  const handleSend = async (message: string) => {
    const appUuid = config.value?.appUuid ?? '';
    const senderIdentifier = sessionStore.getSenderIdentifier(config.value?.userIdentifier, appUuid);
    const chatroomId = chatroomIdRef.current;
    const humanAgentIdentifier = activeAgent?.userIdentifier;

    const userMsg: Message = {
      uuid: crypto.randomUUID(),
      message,
      senderIdentifier,
      chatroomIdentifier: chatroomId,
      createdAt: new Date().toISOString(),
      isOwn: true,
    };
    messagesRef.current = [...messagesRef.current, userMsg];
    humanMessages.value = messagesRef.current;

    sendError.value = null;

    const apiClient = createApiClient(
      config.value?.apiBaseUrl ?? window.location.origin,
      config.value?.token ?? '',
    );

    const result = await apiClient.sendMessage(appUuid, {
      message,
      sender_identifier: senderIdentifier,
      chatroom_identifier: chatroomId,
      send_to_participant: true,
      metadata: humanAgentIdentifier ? { human_agent_identifier: humanAgentIdentifier } : undefined,
    });

    if (result.ok) {
      const newId = String(result.data.chatroom_identifier);
      chatroomIdRef.current = newId;
      sessionStore.setChatroomId(appUuid, newId, 'human');
    } else {
      sendError.value = result.error;
    }
  };

  // List view
  if (!activeAgent) {
    return <AgentList agent={agentInfo.value} onSelect={handleSelectAgent} />;
  }

  // Chat view
  const isOffline = activeAgent.isOnline === false;
  return (
    <div class="flex flex-col h-full">
      {/* Back bar */}
      <div class="flex items-center gap-3 px-3 py-2 border-b border-gray-100 bg-gray-50">
        <button
          onClick={handleBack}
          aria-label="Back to agents"
          class="p-1 rounded hover:bg-gray-200 transition-colors text-gray-600"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-5 h-5">
            <path fill-rule="evenodd" d="M17 10a.75.75 0 0 1-.75.75H5.612l4.158 3.96a.75.75 0 1 1-1.04 1.08l-5.5-5.25a.75.75 0 0 1 0-1.08l5.5-5.25a.75.75 0 1 1 1.04 1.08L5.612 9.25H16.25A.75.75 0 0 1 17 10Z" clip-rule="evenodd" />
          </svg>
        </button>
        <div class="relative flex-shrink-0">
          <div
            class="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-semibold"
            style={{ backgroundColor: 'var(--ch8r-accent)' }}
          >
            {activeAgent.name.charAt(0).toUpperCase()}
          </div>
          <span class={`absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-white ${activeAgent.isOnline ? 'bg-green-400' : 'bg-gray-300'}`} />
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-gray-800 truncate">{activeAgent.name}</p>
          <p class="text-xs text-gray-500">{activeAgent.isOnline ? 'Online' : 'Offline'}</p>
        </div>
      </div>

      {isOffline && (
        <div class="bg-yellow-50 border-b border-yellow-200 px-4 py-2 text-sm text-yellow-800">
          Agent is currently unavailable
        </div>
      )}
      {wsStatus.value === 'error' && (
        <div class="bg-red-50 border-b border-red-200 px-4 py-2 text-sm text-red-800 flex items-center justify-between">
          <span>Connection lost.</span>
          <button
            onClick={() => {
              const appUuid = config.value?.appUuid ?? '';
              const senderIdentifier = sessionStore.getSenderIdentifier(config.value?.userIdentifier, appUuid);
              wsManagerHuman.connect(senderIdentifier, (msg) => {
                const updated = [...messagesRef.current, msg];
                messagesRef.current = updated;
                humanMessages.value = updated;
              }, () => { wsStatus.value = 'error'; }, config.value?.apiBaseUrl);
            }}
            class="ml-3 text-xs font-medium underline hover:no-underline"
          >
            Reconnect
          </button>
        </div>
      )}
      {sendError.value && (
        <div class="bg-red-50 px-4 py-2 text-sm text-red-700">{sendError.value}</div>
      )}
      <MessageList messages={humanMessages.value} isTyping={false} />
      <MessageInput onSend={handleSend} disabled={isOffline} />
    </div>
  );
}
