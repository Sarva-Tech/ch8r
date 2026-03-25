import { useEffect, useRef } from 'preact/hooks';
import { config } from '../store/signals';
import { computePositionStyles } from '../utils/position';
import { Header } from './Header';
import { AssistantChat } from './AssistantChat';
import { SupportForm } from './SupportForm';

interface ChatPanelProps {
  onClose: () => void;
  showSupportForm?: boolean;
}

export function ChatPanel({ onClose, showSupportForm = false }: ChatPanelProps) {
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

  return (
    <div
      ref={panelRef}
      role="dialog"
      aria-modal="true"
      aria-label="Chat panel"
      class="w-[380px] h-[560px] rounded-xl shadow-xl bg-white flex flex-col overflow-hidden ch8r-panel-enter"
      style={computePositionStyles(config.value).panel}
    >
      <Header
        appName={config.value?.appName}
        appDescription={config.value?.appDescription}
        appLogoUrl={config.value?.appLogoUrl}
        onClose={onClose}
      />
      <div class="flex-1 overflow-hidden flex flex-col">
        {showSupportForm ? <SupportForm /> : <AssistantChat />}
      </div>
    </div>
  );
}
