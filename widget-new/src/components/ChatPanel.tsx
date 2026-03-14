import { h } from 'preact';
import { useEffect, useRef } from 'preact/hooks';
import { config, activeMode } from '../store/signals';
import { Header } from './Header';
import { ModeNav } from './ModeNav';
import { HumanAgentChat } from './HumanAgentChat';
import { AIAgentChat } from './AIAgentChat';
import { SupportForm } from './SupportForm';

interface ChatPanelProps {
  onClose: () => void;
}

export function ChatPanel({ onClose }: ChatPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { onClose(); return; }
      if (e.key === 'Tab') {
        const focusable = panelRef.current?.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (!focusable || focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault(); last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault(); first.focus();
        }
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    // Focus first focusable element on open
    const focusable = panelRef.current?.querySelector<HTMLElement>('button, input, textarea');
    focusable?.focus();
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  const position = config.value?.position ?? 'bottom-right';
  const posClass = position === 'bottom-left' ? 'left-4' : 'right-4';

  return (
    <div
      ref={panelRef}
      role="dialog"
      aria-modal="true"
      aria-label="Chat panel"
      class={`fixed bottom-20 ${posClass} w-[380px] h-[560px] rounded-xl shadow-xl bg-white flex flex-col overflow-hidden ch8r-panel-enter`}
      style={{ zIndex: 9998 }}
    >
      <Header
        appName={config.value?.appName}
        appDescription={config.value?.appDescription}
        appLogoUrl={config.value?.appLogoUrl}
        onClose={onClose}
      />
      <ModeNav />
      <div class="flex-1 overflow-hidden flex flex-col">
        {activeMode.value === 'human' && <HumanAgentChat />}
        {activeMode.value === 'ai' && <AIAgentChat />}
        {activeMode.value === 'form' && <SupportForm />}
      </div>
    </div>
  );
}
