import { h } from 'preact';
import { activeMode, unreadHuman, unreadAI } from '../store/signals';
import type { ChatMode } from '../types/index';

const TABS: { label: string; mode: ChatMode }[] = [
  { label: 'Talk to a Human', mode: 'human' },
  { label: 'Ask AI', mode: 'ai' },
  { label: 'Report Issue', mode: 'form' },
];

export function ModeNav() {
  return (
    <div role="tablist" class="flex border-b border-gray-200">
      {TABS.map(({ label, mode }) => {
        const isActive = activeMode.value === mode;
        return (
          <button
            key={mode}
            role="tab"
            aria-selected={isActive}
            onClick={() => { activeMode.value = mode; }}
            class={`relative flex-1 py-2 text-xs font-medium transition-colors ${
              isActive
                ? 'border-b-2 text-gray-900'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            style={isActive ? { borderBottomColor: 'var(--ch8r-accent)', color: 'var(--ch8r-accent)' } : undefined}
          >
            {label}
            {mode === 'human' && unreadHuman.value > 0 && (
              <span class="absolute top-1.5 right-2 w-2 h-2 bg-red-500 rounded-full" />
            )}
            {mode === 'ai' && unreadAI.value > 0 && (
              <span class="absolute top-1.5 right-2 w-2 h-2 bg-red-500 rounded-full" />
            )}
          </button>
        );
      })}
    </div>
  );
}
