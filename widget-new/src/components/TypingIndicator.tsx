import { h } from 'preact';

export function TypingIndicator() {
  return (
    <div class="flex items-start gap-2 px-4 py-1">
      <div class="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 bg-muted text-muted-foreground">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
        </svg>
      </div>
      <div class="flex items-center gap-1 bg-muted rounded-lg px-3 py-2">
        <span class="w-2 h-2 rounded-full bg-muted-foreground opacity-50 animate-bounce" style={{ animationDelay: '0ms' }} />
        <span class="w-2 h-2 rounded-full bg-muted-foreground opacity-50 animate-bounce" style={{ animationDelay: '150ms' }} />
        <span class="w-2 h-2 rounded-full bg-muted-foreground opacity-50 animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
    </div>
  );
}
