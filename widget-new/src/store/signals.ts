import { signal, computed } from '@preact/signals';
import type { Message, WidgetConfig, AgentInfo, ChatroomPreview } from '../types/index';

export const isOpen = signal<boolean>(false);
export const config = signal<WidgetConfig | null>(null);

export const chatrooms = signal<ChatroomPreview[]>([]);
export const messages = signal<Message[]>([]);

export const unreadCount = computed(() =>
  chatrooms.value.filter(c => c.has_unread).length
);

export const isTyping = signal<boolean>(false);
export const wsStatus = signal<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
export const sendError = signal<string | null>(null);
export const agentInfo = signal<AgentInfo | null>(null);

export const aiMode = signal<boolean>(false);
