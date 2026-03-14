import { h } from 'preact';
import { useEffect, useRef } from 'preact/hooks';
import type { Message } from '../types/index';
import { TypingIndicator } from './TypingIndicator';

interface MessageListProps {
  messages: Message[];
  isTyping: boolean;
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
          class={`flex ${msg.isOwn ? 'justify-end' : 'justify-start'}`}
        >
          <div
            class={`max-w-[75%] px-3 py-2 rounded-2xl text-sm break-words ${
              msg.isOwn
                ? 'rounded-br-sm text-white'
                : 'rounded-bl-sm bg-gray-100 text-gray-900'
            }`}
            style={msg.isOwn ? { backgroundColor: 'var(--ch8r-accent)', color: 'var(--ch8r-accent-fg)' } : undefined}
          >
            {msg.message}
          </div>
        </div>
      ))}

      {isTyping && <TypingIndicator />}

      <div ref={bottomRef} />

      {/* ARIA live region for screen readers */}
      <div aria-live="polite" aria-atomic="true" class="sr-only">
        {lastMessage?.message ?? ''}
      </div>
    </div>
  );
}
