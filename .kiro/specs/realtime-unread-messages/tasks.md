# Implementation Plan: Realtime Unread Messages

## Overview

Implement per-participant unread message tracking and real-time delivery across the Django backend, Nuxt/Vue dashboard, and Preact widget. The backend is the source of truth; changes propagate via the existing Django Channels WebSocket infrastructure.

## Tasks

- [x] 1. Add `has_unread` field to `ChatroomParticipant` model
  - Add `has_unread = models.BooleanField(default=False)` to `backend/core/models/chatroom_participant.py`
  - Generate migration `0027_chatroomparticipant_has_unread.py`
  - _Requirements: 1.1_

- [x] 2. Implement unread utility functions
  - [x] 2.1 Implement `mark_unread_for_participants` in a new `backend/core/services/unread.py`
    - Use a single atomic `ChatroomParticipant.objects.filter(...).update(has_unread=True)` excluding the sender
    - Return the list of updated `user_identifier` values for broadcasting
    - _Requirements: 1.2, 1.4_

  - [ ]* 2.2 Write property test for `mark_unread_for_participants`
    - **Property 1: Unread flag set for non-senders**
    - **Validates: Requirements 1.2**

  - [x] 2.3 Implement `mark_read_for_participant` in `backend/core/services/unread.py`
    - Atomically set `has_unread=False` for the given `chatroom` + `user_identifier`
    - _Requirements: 1.3, 1.4_

  - [ ]* 2.4 Write property test for `mark_read_for_participant`
    - **Property 2: Mark-read clears unread flag**
    - **Property 3: Unread round-trip (set then clear)**
    - **Validates: Requirements 1.3, 1.4**

  - [x] 2.5 Implement `broadcast_unread_update` in `backend/core/services/unread.py`
    - Wrap `async_to_sync(channel_layer.group_send)` with try/except; log warning on failure and continue
    - Group name: `live_{user_identifier}` using `LIVE_UPDATES_PREFIX`
    - Payload: `{"type": "send.unread_update", "chatroom_uuid": ..., "has_unread": ..., "sender_identifier": ...}`
    - _Requirements: 3.1, 3.5_

- [x] 3. Add `send_unread_update` handler to `LiveUpdatesConsumer`
  - Add `async def send_unread_update(self, event)` to `backend/core/consumers.py`
  - Forward `chatroom_uuid`, `has_unread`, `sender_identifier` as JSON with `type: "unread_update"`
  - _Requirements: 3.4_

  - [ ]* 3.1 Write property test for `send_unread_update` event payload
    - **Property 6: unread_update event payload completeness**
    - **Validates: Requirements 3.2, 3.4**

- [x] 4. Wire unread logic into `SendMessageView` and `ChatRoomMessagesView`
  - [x] 4.1 Call `mark_unread_for_participants` and `broadcast_unread_update` in `backend/core/views/message.py` after `Message` is saved
    - Broadcast to each non-sender participant returned by `mark_unread_for_participants`
    - _Requirements: 1.2, 3.1_

  - [ ]* 4.2 Write property test for WebSocket broadcast on message save
    - **Property 7: WebSocket broadcast on message save**
    - **Validates: Requirements 3.1**

  - [x] 4.3 Call `mark_read_for_participant` and `broadcast_unread_update` in `backend/core/views/chatroom.py` `ChatRoomMessagesView.get`
    - Determine `user_identifier` from `request.user` (authenticated) or widget token participant
    - Broadcast `has_unread=False` to that participant's group
    - _Requirements: 1.3, 3.3_

  - [ ]* 4.4 Write property test for WebSocket broadcast on mark-read
    - **Property 8: WebSocket broadcast on mark-read**
    - **Validates: Requirements 3.3**

- [x] 5. Checkpoint — Ensure all backend tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Expose `has_unread` in chatroom list API serializer and views
  - [x] 6.1 Add `has_unread = serializers.SerializerMethodField()` to `ChatRoomPreviewSerializer` in `backend/core/serializers/chatroom.py`
    - `get_has_unread` looks up `ChatroomParticipant` using `user_identifier` from serializer context; returns `False` if no record found
    - _Requirements: 2.3, 2.4_

  - [ ]* 6.2 Write property test for API response `has_unread` field
    - **Property 4: API response includes has_unread**
    - **Property 5: Missing participant defaults to has_unread=False**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

  - [x] 6.3 Pass `user_identifier` into serializer context in `ApplicationChatRoomsPreviewView` in `backend/core/views/application.py`
    - Use `request.user` identifier as the context value
    - _Requirements: 2.1_

  - [x] 6.4 Pass `sender_identifier` into serializer context in `UserChatRoomsView` in `backend/core/views/application.py`
    - Use the `sender_identifier` query param as the context value
    - _Requirements: 2.2_

- [x] 7. Add `ChatroomPreview` type and `chatrooms` signal to widget
  - [x] 7.1 Add `ChatroomPreview` interface to `widget-new/src/types/index.ts`
    - Fields: `uuid`, `name`, `last_message`, `has_unread: boolean`
    - _Requirements: 5.1_

  - [x] 7.2 Add `chatrooms` signal and derived `unreadCount` computed to `widget-new/src/store/signals.ts`
    - `chatrooms = signal<ChatroomPreview[]>([])`
    - `unreadCount = computed(() => chatrooms.value.filter(c => c.has_unread).length)`
    - Replace `unreadHuman` / `unreadAI` usages with the new derived signal where applicable
    - _Requirements: 6.1, 6.2, 6.3_

- [x] 8. Extend `WebSocketManager` to handle `unread_update` events
  - Add `onUnreadUpdate` callback field and registration method to `widget-new/src/services/websocket.ts`
  - Parse `unread_update` events in `ws.onmessage` and invoke the callback
  - On reconnect, invoke a registered `onReconnect` callback so callers can re-fetch chatrooms
  - _Requirements: 7.1, 7.4, 7.5_

- [x] 9. Build `UnreadBadge` component for the widget
  - Create `widget-new/src/components/UnreadBadge.tsx`
  - Render `<span aria-label="Unread messages" class="w-2.5 h-2.5 bg-red-500 rounded-full" />`
  - _Requirements: 5.5_

- [x] 10. Update `ChatroomList` to read from `chatrooms` signal and show `UnreadBadge`
  - Refactor `widget-new/src/components/ChatroomList.tsx` to populate the `chatrooms` signal on load and subscribe to `unread_update` WebSocket events
  - Render `<UnreadBadge />` on rows where `has_unread` is `true`
  - Optimistically set `has_unread=false` in the signal when a row is selected
  - Re-fetch chatroom list on WebSocket reconnect
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 7.2, 7.3, 7.5_

  - [ ]* 10.1 Write unit tests for `ChatroomList` unread badge rendering
    - Test badge shown when `has_unread=true`, hidden when `false`
    - Test optimistic clear on row selection
    - _Requirements: 5.1, 5.4_

- [x] 11. Update `Launcher` to show aggregate unread badge
  - Read `unreadCount` computed signal in `widget-new/src/components/Launcher.tsx`
  - Render a red dot with `aria-label="You have unread messages"` when `unreadCount > 0`
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ]* 11.1 Write unit tests for `Launcher` aggregate badge
    - Test badge shown when any chatroom has `has_unread=true`
    - Test badge hidden when all chatrooms have `has_unread=false`
    - _Requirements: 6.1, 6.2_

- [x] 12. Checkpoint — Ensure all widget tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Build `UnreadBadge` component for the dashboard
  - Create `frontend/components/UnreadBadge.vue`
  - Render a `<span>` with `aria-label="Unread messages"` and red dot styling
  - _Requirements: 4.5_

- [x] 14. Update `useChatroomStore` to track `has_unread` from API and WebSocket events
  - Add `has_unread: boolean` to the `ChatroomPreview` interface in `frontend/stores/chatrooms.ts`
  - Populate `has_unread` from the API response in `fetchChatrooms`
  - Update `markUnread` / `markRead` actions to set `has_unread` directly on the chatroom object in the `chatrooms` array
  - _Requirements: 4.1, 4.2, 4.3, 8.1, 8.4_

- [x] 15. Subscribe to `unread_update` events in the dashboard chatroom list page
  - In the chatroom list page under `frontend/pages/applications/[appId]/`, subscribe to `unread_update` events via `useLiveUpdateStore`
  - Call `markUnread` / `markRead` on the store based on the event's `has_unread` value
  - Render `<UnreadBadge />` on rows where `has_unread` is `true`
  - Optimistically call `markRead` when the user navigates into a chatroom
  - Re-fetch chatroom list on WebSocket reconnect (subscribe to `useLiveUpdateStore` reconnect)
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 8.2, 8.3, 8.5_

  - [ ]* 15.1 Write unit tests for dashboard chatroom list unread badge
    - Test badge shown/hidden based on `has_unread`
    - Test `unread_update` event triggers badge update
    - _Requirements: 4.1, 4.2, 4.3_

- [x] 16. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Property tests use Hypothesis; annotate each with `# Feature: realtime-unread-messages, Property N: <text>`
- Widget tests use Vitest + @testing-library/preact; dashboard tests use Vitest + Vue Test Utils
- All `broadcast_unread_update` calls must be fire-and-forget (log warning, never raise)
- The `chatrooms` signal in the widget is the single source of truth for unread state; avoid duplicating state in component-local `useState`
