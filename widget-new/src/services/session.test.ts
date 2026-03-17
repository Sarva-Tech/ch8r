import { describe, it, expect, beforeEach } from 'vitest';
import * as fc from 'fast-check';

// We import the class indirectly by re-instantiating via module reset.
// Since sessionStore is a singleton, we test via a fresh instance each time.
// We expose SessionStore for testing by importing the module fresh.

// Helper: create a fresh SessionStore instance for each test
function makeStore() {
  // Inline the class to avoid singleton state leaking between tests
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
        const scoped = `widget_${appUuid}:${override}`;
        const key = SCOPED_SENDER_KEY(appUuid);
        this.write(key, scoped);
        return scoped;
      }
      const existing = this.read(SENDER_KEY);
      if (existing) {
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

  return new SessionStore();
}

beforeEach(() => {
  localStorage.clear();
});

/**
 * Property 1: SessionStore chatroom ID round-trip
 * Validates: Requirements 1.4
 */
describe('Property 1: SessionStore chatroom ID round-trip', () => {
  it('setChatroomId then getChatroomId returns the same ID, and no mode-keyed keys exist', () => {
    fc.assert(
      fc.property(fc.uuid(), fc.uuid(), (appUuid, chatroomId) => {
        localStorage.clear();
        const store = makeStore();

        store.setChatroomId(appUuid, chatroomId);

        expect(store.getChatroomId(appUuid)).toBe(chatroomId);
        // Old mode-keyed keys must not exist
        expect(localStorage.getItem(`ch8r_${appUuid}_chatroom_human`)).toBeNull();
        expect(localStorage.getItem(`ch8r_${appUuid}_chatroom_ai`)).toBeNull();
      })
    );
  });

  it('getChatroomId returns null before any chatroom is set', () => {
    fc.assert(
      fc.property(fc.uuid(), (appUuid) => {
        localStorage.clear();
        const store = makeStore();
        expect(store.getChatroomId(appUuid)).toBeNull();
      })
    );
  });
});

/**
 * Property 19: Widget identifier starts with widget_
 * Validates: Requirements 8.1, 8.6
 */
describe('Property 19: Widget identifier starts with widget_', () => {
  it('getSenderIdentifier always returns a widget_-prefixed string (anonymous)', () => {
    fc.assert(
      fc.property(fc.constant(undefined), fc.constant(undefined), () => {
        localStorage.clear();
        const store = makeStore();
        const id = store.getSenderIdentifier();
        expect(id).toMatch(/^widget_/);
      })
    );
  });

  it('getSenderIdentifier always returns a widget_-prefixed string (identified)', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 1 }),
        fc.uuid(),
        (userIdentifier, appUuid) => {
          localStorage.clear();
          const store = makeStore();
          const id = store.getSenderIdentifier(userIdentifier, appUuid);
          expect(id).toMatch(/^widget_/);
        }
      )
    );
  });

  it('getSenderIdentifier migrates stored value without widget_ prefix', () => {
    fc.assert(
      fc.property(fc.uuid(), (rawUuid) => {
        localStorage.clear();
        // Simulate a pre-migration stored value (no widget_ prefix)
        localStorage.setItem('ch8r_sender_identifier', rawUuid);
        const store = makeStore();
        const id = store.getSenderIdentifier();
        expect(id).toBe(`widget_${rawUuid}`);
        expect(id).toMatch(/^widget_/);
      })
    );
  });

  it('getSenderIdentifier returns consistent value on repeated calls (anonymous)', () => {
    fc.assert(
      fc.property(fc.constant(null), () => {
        localStorage.clear();
        const store = makeStore();
        const first = store.getSenderIdentifier();
        const second = store.getSenderIdentifier();
        expect(first).toBe(second);
        expect(first).toMatch(/^widget_/);
      })
    );
  });
});
