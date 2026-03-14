import { signal, computed } from '@preact/signals';
import type { Message, WidgetConfig, ChatMode, AgentInfo } from '../types/index';

export const isOpen = signal<boolean>(false);
export const activeMode = signal<ChatMode>('human');
export const config = signal<WidgetConfig | null>(null);

export const humanMessages = signal<Message[]>([]);
export const aiMessages = signal<Message[]>([]);

export const isTyping = signal<boolean>(false);
export const wsStatus = signal<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
export const sendError = signal<string | null>(null);
export const agentInfo = signal<AgentInfo | null>(null);

export const activeMessages = computed(() =>
  activeMode.value === 'human' ? humanMessages.value : aiMessages.value
);
