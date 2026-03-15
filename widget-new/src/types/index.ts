export type ChatMode = 'human' | 'ai' | 'form';

export interface WidgetConfig {
  appUuid: string;
  token: string;
  accentColor?: string;
  position?: 'bottom-right' | 'bottom-left';
  title?: string;
  launcherIconUrl?: string;
  aiGreeting?: string;
  apiBaseUrl?: string;
  userIdentifier?: string; // optional: pass email/user-id for cross-browser persistence
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
  send_to_participant: boolean;
  metadata?: Record<string, unknown>;
}

export interface SendMessageResponse {
  uuid: string;
  message: string;
  sender_identifier: string;
  chatroom_identifier: string;
  created_at: string;
  message_status: string;
}

export interface SupportFormRequest {
  name: string;
  email: string;
  subject: string;
  body: string;
  sender_identifier: string;
}
