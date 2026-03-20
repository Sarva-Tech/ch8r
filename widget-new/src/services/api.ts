import type {
  AgentInfo,
  ApiResult,
  ChatroomPreview,
  Message,
  SendMessageRequest,
  SendMessageResponse,
  SupportFormRequest,
} from '../types/index';

export class ApiClient {
  constructor(private baseUrl: string, private token: string) {}

  private get headers(): Record<string, string> {
    return {
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json',
    };
  }

  private async request<T>(url: string, options: RequestInit): Promise<ApiResult<T>> {
    try {
      const response = await fetch(url, { ...options, headers: this.headers });
      if (!response.ok) {
        let error = `HTTP ${response.status}`;
        try {
          const body = await response.json();
          if (body?.detail) error = body.detail;
          else if (body?.error) error = body.error;
        } catch {
          // ignore parse errors
        }
        return { ok: false, error };
      }
      if (response.status === 204 || response.headers.get('content-length') === '0') {
        return { ok: true, data: undefined as T };
      }
      const data: T = await response.json();
      return { ok: true, data };
    } catch (err) {
      const error = err instanceof Error ? err.message : 'Network error';
      return { ok: false, error };
    }
  }

  loadHumanAgent(appUuid: string): Promise<ApiResult<AgentInfo>> {
    return this.request<{ user_identifier: string; name: string; email: string; is_online: boolean }>(
      `${this.baseUrl}/api/applications/${appUuid}/human-agent/`,
      { method: 'GET' },
    ).then(r => r.ok ? {
      ok: true,
      data: {
        userIdentifier: r.data.user_identifier,
        name: r.data.name,
        role: 'Support Agent',
        isOnline: r.data.is_online,
      },
    } : r);
  }

  loadChatrooms(appUuid: string, senderIdentifier: string, type?: 'human' | 'ai'): Promise<ApiResult<ChatroomPreview[]>> {
    const typeParam = type ? `&type=${type}` : '';
    return this.request<{ chatrooms: ChatroomPreview[] }>(
      `${this.baseUrl}/api/applications/${appUuid}/user-chatrooms/?sender_identifier=${encodeURIComponent(senderIdentifier)}${typeParam}`,
      { method: 'GET' },
    ).then(r => r.ok ? { ok: true, data: r.data.chatrooms } : r);
  }

  sendMessage(appUuid: string, req: SendMessageRequest): Promise<ApiResult<SendMessageResponse>> {
    return this.request<SendMessageResponse>(
      `${this.baseUrl}/api/applications/${appUuid}/chatrooms/send-message/`,
      { method: 'POST', body: JSON.stringify(req) },
    );
  }

  loadHistory(appUuid: string, chatroomUuid: string, senderIdentifier: string): Promise<ApiResult<Message[]>> {
    return this.request<{ messages: Array<{
      uuid: string; message: string; sender_identifier: string;
      chatroom_identifier: string; created_at: string;
    }> }>(
      `${this.baseUrl}/api/applications/${appUuid}/chatrooms/${chatroomUuid}/messages/?sender_identifier=${encodeURIComponent(senderIdentifier)}`,
      { method: 'GET' },
    ).then(r => {
      if (!r.ok) return r;
      const messages: Message[] = r.data.messages.map(m => ({
        uuid: m.uuid,
        message: m.message,
        senderIdentifier: m.sender_identifier,
        chatroomIdentifier: String(m.chatroom_identifier),
        createdAt: m.created_at,
        isOwn: m.sender_identifier === senderIdentifier,
      }));
      return { ok: true, data: messages };
    });
  }

  submitSupportForm(appUuid: string, req: SupportFormRequest): Promise<ApiResult<void>> {
    return this.request<void>(
      `${this.baseUrl}/api/apps/${appUuid}/support/`,
      { method: 'POST', body: JSON.stringify(req) },
    );
  }
}

export function createApiClient(baseUrl: string, token: string): ApiClient {
  return new ApiClient(baseUrl, token);
}
