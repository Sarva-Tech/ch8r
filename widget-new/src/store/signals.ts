import { signal, computed } from '@preact/signals';
import type { Message, WidgetConfig, ChatMode, AgentInfo, ChatroomPreview } from '../types/index';

export const isOpen = signal<boolean>(false);
export const activeMode = signal<ChatMode>('human');
export const unreadHuman = signal<number>(0);
export const unreadAI = signal<number>(0);
export const config = signal<WidgetConfig | null>(null);

export const chatrooms = signal<ChatroomPreview[]>([]);
export const chatroomsHuman = signal<ChatroomPreview[]>([]);
export const chatroomsAI = signal<ChatroomPreview[]>([]);
export const unreadCount = computed(() => {
  const allUuids = new Set<string>();
  const combined: ChatroomPreview[] = [];
  for (const c of [...chatroomsHuman.value, ...chatroomsAI.value]) {
    if (!allUuids.has(c.uuid)) { allUuids.add(c.uuid); combined.push(c); }
  }
  return combined.filter(c => c.has_unread).length;
});

export const humanMessages = signal<Message[]>([]);
export const aiMessages = signal<Message[]>([]);

export const isTyping = signal<boolean>(false);
export const wsStatus = signal<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
export const sendError = signal<string | null>(null);
export const agentInfo = signal<AgentInfo | null>(null);

export const activeMessages = computed(() =>
  activeMode.value === 'human' ? humanMessages.value : aiMessages.value
);
