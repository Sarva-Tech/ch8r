import type { Message } from '../types/index';

class WebSocketManager {
  private ws: WebSocket | null = null;
  private retries = 0;
  private readonly maxRetries = 5;
  private senderIdentifier = '';
  private apiBaseUrl: string | undefined = undefined;
  private onMessageCallback: ((msg: Message) => void) | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private onMaxRetriesCallback: (() => void) | null = null;
  // Flag set during intentional disconnect so onclose doesn't trigger reconnect
  private intentionalClose = false;

  connect(
    senderIdentifier: string,
    onMessage: (msg: Message) => void,
    onMaxRetries?: () => void,
    apiBaseUrl?: string,
  ): void {
    // Always tear down any existing socket before opening a new one
    this._closeSocket();

    this.senderIdentifier = senderIdentifier;
    this.apiBaseUrl = apiBaseUrl;
    this.onMessageCallback = onMessage;
    this.onMaxRetriesCallback = onMaxRetries ?? null;
    this.intentionalClose = false;

    let wsHost = window.location.host;
    let wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    if (apiBaseUrl) {
      try {
        const parsed = new URL(apiBaseUrl);
        wsHost = parsed.host;
        wsProtocol = parsed.protocol === 'https:' ? 'wss://' : 'ws://';
      } catch { /* fall back to window.location.host */ }
    }

    const url = `${wsProtocol}${wsHost}/ws/updates/${senderIdentifier}/`;
    const ws = new WebSocket(url);
    this.ws = ws;

    ws.onopen = () => { this.retries = 0; };

    ws.onmessage = (event: MessageEvent) => {
      // Guard: only handle if this is still the active socket
      if (ws !== this.ws) return;
      try {
        const payload = JSON.parse(event.data);
        if (payload?.type === 'message' && payload?.data) {
          const raw = payload.data;
          const msg: Message = {
            uuid: raw.uuid,
            message: raw.message,
            senderIdentifier: raw.sender_identifier,
            chatroomIdentifier: raw.chatroom_identifier ?? raw.chatroom ?? '',
            createdAt: raw.created_at,
            isOwn: false,
          };
          this.onMessageCallback?.(msg);
        }
      } catch { /* ignore malformed */ }
    };

    ws.onclose = () => {
      if (ws !== this.ws) return; // stale socket, ignore
      if (!this.intentionalClose) this.scheduleReconnect();
    };

    ws.onerror = () => {
      if (ws !== this.ws) return;
      // onclose will fire after onerror, so reconnect is handled there
    };
  }

  disconnect(): void {
    this._clearReconnectTimer();
    this.intentionalClose = true;
    this._closeSocket();
    this.retries = 0;
  }

  private _closeSocket(): void {
    if (this.ws) {
      // Null out first so stale onclose handlers are ignored
      const old = this.ws;
      this.ws = null;
      if (old.readyState === WebSocket.OPEN || old.readyState === WebSocket.CONNECTING) {
        old.close();
      }
    }
  }

  private _clearReconnectTimer(): void {
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.retries >= this.maxRetries) {
      this.onMaxRetriesCallback?.();
      return;
    }
    const delay = Math.min(1000 * Math.pow(2, this.retries), 30_000);
    this.retries++;
    this._clearReconnectTimer();
    this.reconnectTimer = setTimeout(() => {
      if (this.senderIdentifier && this.onMessageCallback) {
        this.connect(this.senderIdentifier, this.onMessageCallback, this.onMaxRetriesCallback ?? undefined, this.apiBaseUrl);
      }
    }, delay);
  }
}

export const wsManager = new WebSocketManager();
export const wsManagerHuman = new WebSocketManager();
