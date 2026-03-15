import { h } from 'preact';
import { useEffect, useRef } from 'preact/hooks';
import type { Message } from '../types/index';
import { TypingIndicator } from './TypingIndicator';

interface MessageListProps {
  messages: Message[];
  isTyping: boolean;
}

function BotIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 8V4H8"/>
      <rect width="16" height="12" x="4" y="8" rx="2"/>
      <path d="M2 14h2"/><path d="M20 14h2"/>
      <path d="M15 13v2"/><path d="M9 13v2"/>
    </svg>
  );
}

function HumanAgentIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="8" r="4"/>
      <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
    </svg>
  );
}

function WidgetUserIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>
      <circle cx="12" cy="7" r="4"/>
    </svg>
  );
}

function Avatar({ senderIdentifier, isOwn }: { senderIdentifier: string; isOwn: boolean }) {
  const isAI = senderIdentifier.startsWith('agent_llm');
  const isHumanAgent = !isOwn && !isAI;

  if (isOwn) {
    return (
      <div class="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: '#d1fae5' }}>
        <WidgetUserIcon />
      </div>
    );
  }
  if (isAI) {
    return (
      <div class="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: '#ede9fe' }}>
        <BotIcon />
      </div>
    );
  }
  return (
    <div class="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: '#dbeafe' }}>
      <HumanAgentIcon />
    </div>
  );
}

export function MessageList({ messages, isTyping }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const lastMessage = messages[messages.length - 1];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  return (
    <div class="flex-1 overflow-y-auto flex flex-col gap-2 px-4 py-3">
      {messages.map((msg) => (
        <div
          key={msg.uuid}
          class={`flex items-end gap-2 ${msg.isOwn ? 'flex-row-reverse' : 'flex-row'}`}
        >
          <Avatar senderIdentifier={msg.senderIdentifier} isOwn={msg.isOwn} />
          <div class={`flex flex-col gap-0.5 max-w-[75%] ${msg.isOwn ? 'items-end' : 'items-start'}`}>
            <div
              class={`px-3 py-2 rounded-2xl text-sm break-words ${
                msg.isOwn
                  ? 'rounded-br-sm text-white'
                  : 'rounded-bl-sm bg-gray-100 text-gray-900'
              }`}
              style={msg.isOwn ? { backgroundColor: 'var(--ch8r-accent)', color: 'var(--ch8r-accent-fg)' } : undefined}
            >
              {msg.message}
            </div>
            <span class="text-xs text-gray-400 px-1">
              {new Date(msg.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        </div>
      ))}

      {isTyping && <TypingIndicator />}

      <div ref={bottomRef} />

      <div aria-live="polite" aria-atomic="true" class="sr-only">
        {lastMessage?.message ?? ''}
      </div>
    </div>
  );
}
