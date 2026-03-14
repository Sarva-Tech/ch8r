# Implementation Plan: Embeddable Chat Widget

## Overview

Implement the `widget-new` package as a Vite + Preact + TypeScript IIFE bundle with Shadow DOM isolation, Preact Signals state management, three chat modes (Human Agent via WebSocket, AI Agent via REST, Support Form), and full localStorage session persistence. Tests use Vitest + @testing-library/preact + fast-check.

## Tasks

- [x] 1. Project scaffolding
  - Create `widget-new/package.json` with Preact, Vite, TypeScript, Tailwind, fast-check, Vitest, @testing-library/preact dependencies
  - Create `widget-new/vite.config.ts` with IIFE lib build, `@preact/vite-plugin-preact`, terser minification, and `inlineDynamicImports: true`
  - Create `widget-new/tsconfig.json` targeting ES2020, JSX preset for Preact
  - Create `widget-new/tailwind.config.ts` scanning `src/**/*.{ts,tsx}`
  - Create `widget-new/vitest.config.ts` with jsdom environment and @testing-library/preact setup
  - _Requirements: 1.1, 10.1_

- [x] 2. Types and data models
  - [x] 2.1 Create `src/types/index.ts` with all TypeScript interfaces and types
    - Define `ChatMode`, `WidgetConfig`, `Message`, `AgentInfo`, `SupportFormData`, `SupportFormErrors`
    - Define `ApiResult<T>` discriminated union, `SendMessageRequest`, `SendMessageResponse`, `SupportFormRequest`
    - _Requirements: 1.6, 4.4, 6.1_

- [x] 3. Services layer
  - [x] 3.1 Implement `src/services/session.ts` — `SessionStore` class
    - `getSenderIdentifier()`: read or generate+persist UUID v4 under `ch8r_sender_identifier`
    - `getChatroomId(appUuid)` / `setChatroomId(appUuid, id)`: read/write `ch8r_{appUuid}_chatroom_human`
    - `getMessages(appUuid, mode)` / `setMessages(appUuid, mode, msgs)`: read/write `ch8r_{appUuid}_messages_{mode}`
    - Wrap all `localStorage` calls in try/catch; fall back to in-memory Map on failure
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 3.2 Write property tests for SessionStore
    - **Property 19: Sender identifier idempotence**
    - **Validates: Requirements 7.1, 7.2**
    - **Property 20: SessionStore round-trip for messages and chatroom ID**
    - **Validates: Requirements 7.3, 7.4, 7.5**

  - [ ]* 3.3 Write unit tests for SessionStore
    - Test UUID generation on first call, reuse on subsequent calls
    - Test localStorage unavailability fallback (in-memory)
    - _Requirements: 7.1, 7.2_

  - [x] 3.4 Implement `src/services/api.ts` — `ApiClient` class
    - Constructor accepts `baseUrl` and `token`; all requests include `Authorization: Bearer <token>` header
    - `sendMessage(appUuid, req): Promise<ApiResult<SendMessageResponse>>`
    - `loadHistory(appUuid, chatroomUuid): Promise<ApiResult<Message[]>>`
    - `submitSupportForm(appUuid, req): Promise<ApiResult<void>>`
    - Return `{ ok: false, error }` on non-2xx or network failure
    - _Requirements: 4.4, 4.7, 5.2, 5.4, 6.2, 6.5_

  - [ ]* 3.5 Write unit tests for ApiClient
    - Test correct `Authorization` header on all requests
    - Test correct request body shape for `sendMessage` and `submitSupportForm`
    - Test `{ ok: false }` result on non-2xx response
    - _Requirements: 4.4, 4.7_

  - [x] 3.6 Implement `src/services/websocket.ts` — `WebSocketManager` class
    - `connect(senderIdentifier, onMessage)`: open `ws://{host}/ws/updates/{senderIdentifier}/`
    - `disconnect()`: close connection and clear retry state
    - Exponential backoff on `onerror`/`onclose`: `delay = min(1000 * 2^n, 30000)` ms, max 5 retries
    - After 5 failures set `wsStatus` signal to `'error'`
    - _Requirements: 4.8, 4.9_

  - [ ]* 3.7 Write property tests for WebSocketManager
    - **Property 13: WebSocket URL includes sender_identifier**
    - **Validates: Requirements 4.8**
    - **Property 14: Exponential backoff on WebSocket reconnect**
    - **Validates: Requirements 4.9**

  - [ ]* 3.8 Write unit tests for WebSocketManager
    - Test URL construction with arbitrary sender identifiers
    - Test reconnect scheduling and retry counter increment
    - _Requirements: 4.8, 4.9_

- [ ] 4. Checkpoint — Ensure all service tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Signals store
  - [x] 5.1 Create `src/store/signals.ts` with all Preact Signals
    - `isOpen`, `activeMode`, `config`, `humanMessages`, `aiMessages`, `isTyping`, `wsStatus`, `sendError`, `agentInfo`
    - `activeMessages` computed signal derived from `activeMode`
    - _Requirements: 3.3, 5.5_

  - [ ]* 5.2 Write property tests for signals store
    - **Property 2: Launcher visibility is the inverse of panel open state**
    - **Validates: Requirements 2.2, 2.4**
    - **Property 7: Mode switch preserves independent message histories**
    - **Validates: Requirements 3.3, 5.5**

- [x] 6. Styles
  - [x] 6.1 Create `src/styles/base.css` with Tailwind directives and CSS custom properties
    - Define `:host` CSS vars: `--ch8r-accent`, `--ch8r-accent-fg`, `--ch8r-radius`, `--ch8r-font`
    - Include `@tailwind base`, `@tailwind components`, `@tailwind utilities`
    - _Requirements: 8.1, 8.4_

- [x] 7. Core components
  - [x] 7.1 Implement `src/components/Launcher.tsx`
    - Fixed-position FAB, bottom-right by default; accepts `position`, `accentColor`, `iconUrl`, `onOpen`
    - Hidden when `isOpen` is true; renders `<img>` when `iconUrl` provided
    - `aria-label="Open chat"` attribute
    - _Requirements: 2.1, 2.2, 2.4, 2.5, 2.6, 8.3, 9.1_

  - [ ]* 7.2 Write property tests for Launcher
    - **Property 2: Launcher visibility is the inverse of panel open state**
    - **Validates: Requirements 2.2, 2.4**
    - **Property 3: Clicking the Launcher opens the panel**
    - **Validates: Requirements 2.3**
    - **Property 4: Custom position applied to Launcher**
    - **Validates: Requirements 2.5**
    - **Property 22: Custom launcher icon rendered**
    - **Validates: Requirements 8.3**

  - [ ]* 7.3 Write unit tests for Launcher
    - Test `aria-label` presence
    - Test icon `<img>` rendered when `iconUrl` provided
    - Test default position is `bottom-right`
    - _Requirements: 2.1, 8.3, 9.1_

  - [x] 7.4 Implement `src/components/Header.tsx`
    - Renders agent name, role, online status indicator, close button
    - Displays custom `title` from config when provided
    - `onClose` callback on close button click
    - _Requirements: 3.1, 3.4, 4.1, 4.2, 8.2_

  - [ ]* 7.5 Write property tests for Header
    - **Property 6: Header renders agent info correctly**
    - **Validates: Requirements 3.1, 4.1, 4.2, 5.1**
    - **Property 21: Custom title rendered in header**
    - **Validates: Requirements 8.2**

  - [x] 7.6 Implement `src/components/ModeNav.tsx`
    - Tab bar with three tabs: Human, AI, Form
    - Updates `activeMode` signal on tab click
    - _Requirements: 3.2_

  - [x] 7.7 Implement `src/components/TypingIndicator.tsx`
    - Animated three-dot indicator; rendered when `isTyping` is true
    - _Requirements: 5.2_

  - [x] 7.8 Implement `src/components/MessageList.tsx`
    - Scrollable list of message bubbles; own messages right-aligned, agent messages left-aligned
    - ARIA live region (`aria-live="polite"`) containing the latest message text
    - Auto-scrolls to bottom on new message
    - Renders `<TypingIndicator />` when `isTyping` is true
    - _Requirements: 4.6, 9.3_

  - [ ]* 7.9 Write property tests for MessageList
    - **Property 12: WebSocket message appended to humanMessages**
    - **Validates: Requirements 4.6**
    - **Property 23: New messages announced via ARIA live region**
    - **Validates: Requirements 9.3**

  - [x] 7.10 Implement `src/components/MessageInput.tsx`
    - Textarea + send button; calls `onSend(text)` on submit (Enter key or button click)
    - Disabled when `disabled` prop is true
    - _Requirements: 4.4, 9.5_

- [x] 8. Mode-specific components
  - [x] 8.1 Implement `src/components/HumanAgentChat.tsx`
    - On mount: call `WebSocketManager.connect(senderIdentifier, onMessage)`; load history from `SessionStore`
    - On unmount: call `WebSocketManager.disconnect()`
    - `onMessage` handler appends to `humanMessages` signal and persists via `SessionStore`
    - On send: call `ApiClient.sendMessage`; persist returned `chatroomIdentifier` via `SessionStore`
    - Render offline banner when `agentInfo.isOnline` is false
    - Render error banner with "Reconnect" button when `wsStatus` is `'error'`
    - Render inline send error when `sendError` is set
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9_

  - [ ]* 8.2 Write property tests for HumanAgentChat
    - **Property 9: Offline agent shows unavailability message**
    - **Validates: Requirements 4.3**
    - **Property 10: Send message request includes correct identifiers**
    - **Validates: Requirements 4.4**
    - **Property 11: Chatroom ID persisted after creation**
    - **Validates: Requirements 4.5**

  - [x] 8.3 Implement `src/components/AIAgentChat.tsx`
    - On first open in session: display `aiGreeting` from config
    - On send: set `isTyping = true`, call `ApiClient.sendMessage`, append response to `aiMessages`, set `isTyping = false`
    - On error: set `sendError`, set `isTyping = false`
    - Load AI message history from `SessionStore` on mount
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ]* 8.4 Write property tests for AIAgentChat
    - **Property 15: isTyping is true during an in-flight AI request**
    - **Validates: Requirements 5.2**
    - **Property 16: AI response round-trip**
    - **Validates: Requirements 5.3**

  - [x] 8.5 Implement `src/components/SupportForm.tsx`
    - Fields: name, email, subject, body — each with `<label for=...>` and matching `id`
    - Client-side validation: non-empty required fields, valid email regex
    - On validation failure: set `SupportFormErrors` and render field-level error messages
    - On success: call `ApiClient.submitSupportForm`, display confirmation, reset fields
    - On API failure: display error, preserve entered data
    - Keyboard-navigable; all fields reachable via Tab
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 9.5_

  - [ ]* 8.6 Write property tests for SupportForm
    - **Property 17: Support form validation rejects invalid inputs**
    - **Validates: Requirements 6.2, 6.3**
    - **Property 18: Successful form submission resets form state**
    - **Validates: Requirements 6.4**

  - [ ]* 8.7 Write unit tests for SupportForm
    - Test each field has a `<label>` with matching `for`/`id`
    - Test all four fields render
    - Test validation error display per field
    - _Requirements: 6.1, 6.6_

- [ ] 9. Checkpoint — Ensure all component tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. ChatPanel and App assembly
  - [x] 10.1 Implement `src/components/ChatPanel.tsx`
    - Renders `<Header />`, `<ModeNav />`, `<MessageList />`, `<MessageInput />`, and the active mode view
    - Traps keyboard focus within the panel while open; returns focus to Launcher on close
    - Handles Escape key to call `onClose`
    - Animated slide-up open/close transition
    - _Requirements: 3.1, 3.2, 3.4, 3.5, 9.2, 9.5, 9.6_

  - [ ]* 10.2 Write property tests for ChatPanel
    - **Property 8: Any close action sets isOpen to false**
    - **Validates: Requirements 3.4, 3.5, 9.6**

  - [x] 10.3 Implement `src/components/App.tsx`
    - Reads `config` signal; renders `<Launcher />` and `<ChatPanel />` conditionally on `isOpen`
    - Applies `--ch8r-accent` CSS custom property to shadow host on config change
    - Defers WebSocket connection and history loading until first panel open
    - _Requirements: 1.6, 2.2, 2.4, 8.1, 10.2, 10.3_

  - [ ]* 10.4 Write property tests for App
    - **Property 5: Accent color applied as CSS custom property**
    - **Validates: Requirements 2.6, 8.1, 8.4**
    - **Property 24: Deferred initialization**
    - **Validates: Requirements 10.2**

- [x] 11. Main entry point
  - [x] 11.1 Implement `src/main.ts` — IIFE entry point
    - Read `data-app-uuid` and `data-token` from the `<script>` tag or `window.Ch8rWidgetConfig`
    - If either is missing: log `[Ch8rWidget] Missing required configuration: appUuid and token are required.` and return
    - Create `<div id="ch8r-widget-root">`, attach Shadow DOM (`mode: 'open'`)
    - Inject compiled Tailwind CSS string as `<style>` into Shadow DOM
    - Set `--ch8r-accent` and other theme CSS vars on shadow host from config
    - Render `<App />` into a `<div>` inside the Shadow DOM
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

  - [ ]* 11.2 Write property tests for main entry point
    - **Property 1: Shadow DOM containment**
    - **Validates: Requirements 1.2, 1.3, 1.5**

  - [ ]* 11.3 Write unit tests for main entry point
    - Test config parsed from `data-app-uuid` / `data-token` attributes (E1)
    - Test missing config → no render, console error logged (E2)
    - _Requirements: 1.6, 1.7_

- [ ] 12. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Property tests use fast-check with a minimum of 100 iterations per property
- Each property test must include the tag comment: `// Feature: embeddable-chat-widget, Property {N}: {property_text}`
- Unit tests use Vitest + @testing-library/preact with jsdom
- `widget.css` (generated by Tailwind CLI) is gitignored; run `npm run build:css` before `npm run build`
