export type WidgetPosition = 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';

export interface WidgetConfig {
  appUuid: string;
  token: string;
  accentColor?: string;
  position?: WidgetPosition;
  offsetTop?: number;
  offsetBottom?: number;
  offsetLeft?: number;
  offsetRight?: number;
  title?: string;
  launcherIconUrl?: string;
  aiGreeting?: string;
  apiBaseUrl?: string;
  userIdentifier?: string;
  appName?: string;
  appDescription?: string;
  appLogoUrl?: string;
}

export interface Message {
  uuid: string;
  message: string;
  senderIdentifier: string;
  chatroomIdentifier: string;
  createdAt: string;
  isOwn: boolean;
  aiMode?: boolean;
}

export interface AgentInfo {
  name: string;
  role: string;
  isOnline: boolean;
  avatarUrl?: string;
  userIdentifier: string;
}

export interface SupportFormData {
  name: string;
  email: string;
  subject: string;
  body: string;
}

export interface SupportFormErrors {
  name?: string;
  email?: string;
  subject?: string;
  body?: string;
}

export interface ChatroomPreview {
  uuid: string;
  name: string;
  has_unread: boolean;
  last_message: {
    uuid: string;
    message: string;
    sender_identifier: string;
    created_at: string;
  } | null;
}

export type ApiResult<T> = { ok: true; data: T } | { ok: false; error: string };

export interface SendMessageRequest {
  message: string;
  sender_identifier: string;
  chatroom_identifier: string | 'new_chat';
  ai_mode?: boolean;
  metadata?: Record<string, unknown>;
}

export interface SendMessageResponse {
  uuid: string;
  message: string;
  sender_identifier: string;
  chatroom_identifier: string;
  created_at: string;
  message_status: string;
  llm_processing?: boolean;
}

export interface SupportFormRequest {
  name: string;
  email: string;
  subject: string;
  body: string;
  sender_identifier: string;
}
