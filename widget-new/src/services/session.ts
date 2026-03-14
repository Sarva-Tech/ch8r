import type { Message } from '../types/index';

const SENDER_KEY = 'ch8r_sender_identifier';
const SCOPED_SENDER_KEY = (appUuid: string) => `ch8r_sender_${appUuid}`;

class SessionStore {
  private fallback = new Map<string, string>();

  private read(key: string): string | null {
    try {
      return localStorage.getItem(key);
    } catch {
      return this.fallback.get(key) ?? null;
    }
  }

  private write(key: string, value: string): void {
    try {
      localStorage.setItem(key, value);
    } catch {
      this.fallback.set(key, value);
    }
  }

  getSenderIdentifier(override?: string, appUuid?: string): string {
    if (override && appUuid) {
      // Scoped identifier: keyed per-app so it never collides with other apps or anonymous sessions
      const scoped = `${appUuid}:${override}`;
      const key = SCOPED_SENDER_KEY(appUuid);
      this.write(key, scoped);
      return scoped;
    }
    // Anonymous fallback: random UUID persisted per browser
    const existing = this.read(SENDER_KEY);
    if (existing) return existing;
    const id = crypto.randomUUID();
    this.write(SENDER_KEY, id);
    return id;
  }

  getChatroomId(appUuid: string, mode: 'human' | 'ai' = 'human'): string | null {
    return this.read(`ch8r_${appUuid}_chatroom_${mode}`);
  }

  setChatroomId(appUuid: string, id: string, mode: 'human' | 'ai' = 'human'): void {
    this.write(`ch8r_${appUuid}_chatroom_${mode}`, id);
  }

  getMessages(appUuid: string, mode: 'human' | 'ai'): Message[] {
    const raw = this.read(`ch8r_${appUuid}_messages_${mode}`);
    if (!raw) return [];
    try {
      return JSON.parse(raw) as Message[];
    } catch {
      return [];
    }
  }

  setMessages(appUuid: string, mode: 'human' | 'ai', msgs: Message[]): void {
    this.write(`ch8r_${appUuid}_messages_${mode}`, JSON.stringify(msgs));
  }
}

export const sessionStore = new SessionStore();
