import { h } from 'preact';

export function TypingIndicator() {
  return (
    <div class="flex items-end gap-1 px-4 py-2">
      <div class="flex items-center gap-1 bg-gray-100 rounded-2xl rounded-bl-sm px-3 py-2">
        <span class="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '0ms' }} />
        <span class="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '150ms' }} />
        <span class="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
    </div>
  );
}
