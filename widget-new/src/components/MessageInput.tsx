import { h } from 'preact';
import { useState } from 'preact/hooks';

interface MessageInputProps {
  onSend: (text: string) => void;
  disabled?: boolean;
  aiMode: boolean;
  onAiModeChange: (v: boolean) => void;
}

export function MessageInput({ onSend, disabled = false, aiMode, onAiModeChange }: MessageInputProps) {
  const [text, setText] = useState('');

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setText('');
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div class="flex flex-col border-t border-gray-200">
      <div class="flex items-center gap-2 px-3 pt-2">
        <label class="flex items-center gap-2 cursor-pointer select-none text-xs text-gray-600">
          <div
            role="switch"
            aria-checked={aiMode}
            aria-label="AI Mode"
            onClick={() => onAiModeChange(!aiMode)}
            class={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors cursor-pointer ${aiMode ? 'bg-purple-500' : 'bg-gray-300'}`}
          >
            <span class={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${aiMode ? 'translate-x-4' : 'translate-x-1'}`} />
          </div>
          AI Mode
        </label>
      </div>
      <div class="flex items-end gap-2 px-3 py-3">
        <textarea
          aria-label="Message input"
          value={text}
          onInput={(e) => setText((e.target as HTMLTextAreaElement).value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          rows={1}
          placeholder="Type a message…"
          class="flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ maxHeight: '120px' }}
        />
        <button
          aria-label="Send message"
          onClick={handleSend}
          disabled={disabled || !text.trim()}
          class="flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center transition-opacity disabled:opacity-40 disabled:cursor-not-allowed"
          style={{ backgroundColor: 'var(--ch8r-accent)', color: 'var(--ch8r-accent-fg)' }}
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4" aria-hidden="true">
            <path d="M3.478 2.405a.75.75 0 0 0-.926.94l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.405Z" />
          </svg>
        </button>
      </div>
    </div>
  );
}
