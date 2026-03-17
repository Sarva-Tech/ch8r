const SENDER_KEY = 'ch8r_sender_identifier';
const SCOPED_SENDER_KEY = (appUuid: string) => `ch8r_sender_${appUuid}`;
const CHATROOM_KEY = (appUuid: string) => `ch8r_${appUuid}_chatroom`;

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
      const scoped = `widget_${appUuid}:${override}`;
      const key = SCOPED_SENDER_KEY(appUuid);
      this.write(key, scoped);
      return scoped;
    }
    // Anonymous fallback: random UUID persisted per browser, always widget_ prefixed
    const existing = this.read(SENDER_KEY);
    if (existing) {
      // Migration: add widget_ prefix if missing
      if (!existing.startsWith('widget_')) {
        const prefixed = `widget_${existing}`;
        this.write(SENDER_KEY, prefixed);
        return prefixed;
      }
      return existing;
    }
    const id = `widget_${crypto.randomUUID()}`;
    this.write(SENDER_KEY, id);
    return id;
  }

  getChatroomId(appUuid: string): string | null {
    return this.read(CHATROOM_KEY(appUuid));
  }

  setChatroomId(appUuid: string, id: string): void {
    this.write(CHATROOM_KEY(appUuid), id);
  }
}

export const sessionStore = new SessionStore();
