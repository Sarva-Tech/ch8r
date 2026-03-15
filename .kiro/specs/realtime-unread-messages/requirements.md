# Requirements Document

## Introduction

This feature adds real-time unread message tracking and live update delivery to both the dashboard and the embeddable chat widget. When a new message arrives in a chatroom, all connected participants receive it instantly via WebSocket. Unread state is persisted per participant on the `ChatroomParticipant` model and is cleared when the user opens that chatroom. The widget launcher icon and each chatroom row in both the widget and dashboard display visual unread indicators driven by this live state.

## Glossary

- **Dashboard**: The authenticated web application used by human agents and app owners to manage chatrooms.
- **Widget**: The embeddable JavaScript chat widget that runs on third-party sites (`widget-new` directory), built with Preact.
- **Launcher**: The floating button rendered by the Widget that opens the chat panel.
- **ChatroomParticipant**: The Django model (`core/models/chatroom_participant.py`) that links a user identifier to a chatroom with a role.
- **UnreadFlag**: A boolean field (`has_unread`) on `ChatroomParticipant` that is `True` when the participant has received at least one message since last viewing the chatroom.
- **LiveUpdatesConsumer**: The Django Channels WebSocket consumer (`core/consumers.py`) that pushes events to connected clients.
- **Channel_Layer**: The Django Channels in-memory or Redis layer used to broadcast messages to WebSocket groups.
- **Sender_Identifier**: The string identifier for a widget user (e.g. `anon_<uuid>` or a registered user id).
- **LIVE_UPDATES_PREFIX**: The constant `"live"` used to construct WebSocket group names.
- **UnreadBadge**: A red circular indicator rendered in the UI when `has_unread` is `True` for a chatroom.
- **UnreadCount**: An integer count of chatrooms with unread messages, shown on the Launcher icon.

---

## Requirements

### Requirement 1: Persist Unread State on ChatroomParticipant

**User Story:** As a system, I want to track whether each participant has unread messages in a chatroom, so that unread indicators can be shown accurately across sessions and clients.

#### Acceptance Criteria

1. THE `ChatroomParticipant` model SHALL include a boolean field `has_unread` with a default value of `False`.
2. WHEN a new `Message` is saved to a chatroom, THE System SHALL set `has_unread = True` on all `ChatroomParticipant` records for that chatroom whose `user_identifier` does not match the message `sender_identifier`.
3. WHEN a participant opens a chatroom (i.e. the chatroom detail or messages endpoint is accessed by that participant), THE System SHALL set `has_unread = False` on the corresponding `ChatroomParticipant` record.
4. THE System SHALL update `has_unread` atomically to prevent race conditions when multiple messages arrive concurrently.

---

### Requirement 2: Include Unread Status in Chatroom List API Responses

**User Story:** As a client (dashboard or widget), I want chatroom list responses to include unread status per chatroom, so that I can render unread indicators without a separate request.

#### Acceptance Criteria

1. WHEN the `ApplicationChatRoomsPreviewView` endpoint is called by an authenticated dashboard user, THE API SHALL include an `has_unread` boolean field in each chatroom object in the response.
2. WHEN the `UserChatRoomsView` endpoint is called with a `sender_identifier`, THE API SHALL include an `has_unread` boolean field in each chatroom object in the response, reflecting the unread state for that specific participant.
3. THE `ChatRoomPreviewSerializer` SHALL expose the `has_unread` field derived from the requesting participant's `ChatroomParticipant` record.
4. IF no `ChatroomParticipant` record exists for the requesting user in a given chatroom, THEN THE API SHALL return `has_unread` as `False` for that chatroom.

---

### Requirement 3: Broadcast Unread State Change Events via WebSocket

**User Story:** As a connected client, I want to receive a WebSocket event when my unread status changes in a chatroom, so that the UI updates in real time without polling.

#### Acceptance Criteria

1. WHEN a new `Message` is saved and `has_unread` is set to `True` for a participant, THE `LiveUpdatesConsumer` SHALL send an `unread_update` event to that participant's WebSocket group.
2. THE `unread_update` event payload SHALL contain the fields: `chatroom_uuid` (string), `has_unread` (boolean `True`), and `sender_identifier` (string identifying who sent the message).
3. WHEN a participant marks a chatroom as read (opens it), THE System SHALL send an `unread_update` event with `has_unread: False` and `chatroom_uuid` to that participant's WebSocket group.
4. THE `LiveUpdatesConsumer` SHALL handle an `unread_update` event type and forward it to the connected WebSocket client as a JSON message with `type: "unread_update"`.
5. IF the Channel_Layer group send fails for a participant, THEN THE System SHALL log a warning and continue processing remaining participants without raising an exception.

---

### Requirement 4: Dashboard Chatroom List Shows Per-Chatroom Unread Indicator

**User Story:** As a human agent using the dashboard, I want to see an unread indicator on each chatroom row in the chatroom list, so that I know which conversations have new messages.

#### Acceptance Criteria

1. WHEN the dashboard chatroom list is rendered, THE Dashboard SHALL display an UnreadBadge on each chatroom row where `has_unread` is `True`.
2. WHEN an `unread_update` WebSocket event is received with `has_unread: True` for a chatroom, THE Dashboard SHALL update the chatroom row to show the UnreadBadge without a full page reload.
3. WHEN an `unread_update` WebSocket event is received with `has_unread: False` for a chatroom, THE Dashboard SHALL remove the UnreadBadge from that chatroom row.
4. WHEN the dashboard user opens a chatroom, THE Dashboard SHALL optimistically clear the UnreadBadge for that chatroom immediately upon navigation.
5. THE UnreadBadge SHALL be visually distinct (red dot) and accessible with an `aria-label` of `"Unread messages"`.

---

### Requirement 5: Widget Chatroom List Shows Per-Chatroom Unread Indicator

**User Story:** As a widget user, I want to see an unread indicator on each chatroom row in the widget's chatroom list, so that I know which conversations have new messages.

#### Acceptance Criteria

1. WHEN the `ChatroomList` component renders a chatroom row, THE Widget SHALL display an UnreadBadge on rows where `has_unread` is `True` in the loaded chatroom data.
2. WHEN an `unread_update` WebSocket event is received with `has_unread: True` for a chatroom, THE Widget SHALL update the corresponding chatroom row to show the UnreadBadge in real time.
3. WHEN an `unread_update` WebSocket event is received with `has_unread: False` for a chatroom, THE Widget SHALL remove the UnreadBadge from the corresponding chatroom row.
4. WHEN the widget user selects a chatroom from the list, THE Widget SHALL optimistically clear the UnreadBadge for that chatroom immediately upon selection.
5. THE UnreadBadge in the chatroom list SHALL be a red dot and SHALL include `aria-label="Unread messages"`.

---

### Requirement 6: Widget Launcher Icon Shows Aggregate Unread Indicator

**User Story:** As a widget user, I want to see a red dot on the Launcher icon when any chatroom has unread messages, so that I know there is activity without opening the widget.

#### Acceptance Criteria

1. WHEN one or more chatrooms have `has_unread: True` for the current Sender_Identifier, THE Launcher SHALL display a red dot badge on the launcher button.
2. WHEN all chatrooms have `has_unread: False`, THE Launcher SHALL not display the red dot badge.
3. WHEN an `unread_update` WebSocket event is received, THE Widget SHALL recompute the aggregate unread count and update the Launcher badge accordingly.
4. THE Launcher badge SHALL be a red circular element overlaid on the top-right of the launcher button and SHALL include `aria-label="You have unread messages"`.
5. WHEN the widget panel is opened and all chatrooms are viewed, THE Launcher SHALL remove the red dot badge once all unread states are cleared.

---

### Requirement 7: Widget Receives Real-Time Message Updates While Embedded

**User Story:** As a widget user on an embedded site, I want new messages to appear in the widget in real time, so that I do not need to refresh the page to see new responses.

#### Acceptance Criteria

1. WHILE the Widget is connected via WebSocket, THE `WebSocketManager` SHALL deliver incoming `message` events to the active chatroom message list in real time.
2. WHEN a `message` WebSocket event is received for a chatroom that is not currently open in the Widget, THE Widget SHALL increment the unread state for that chatroom and update the UnreadBadge and Launcher badge.
3. WHEN a `message` WebSocket event is received for the currently open chatroom, THE Widget SHALL append the message to the message list and SHALL NOT mark that chatroom as unread.
4. THE Widget SHALL maintain the WebSocket connection with exponential back-off reconnection (up to 5 retries, max 30-second delay) as currently implemented.
5. WHEN the WebSocket reconnects after a disconnection, THE Widget SHALL re-fetch the chatroom list to reconcile any unread state changes that occurred while disconnected.

---

### Requirement 8: Dashboard Receives Real-Time Message Updates While Open

**User Story:** As a human agent with the dashboard open, I want new messages to appear and unread counts to update in real time, so that I can respond promptly without refreshing.

#### Acceptance Criteria

1. WHILE the Dashboard is connected via WebSocket, THE Dashboard SHALL receive `message` events and update the relevant chatroom's last message preview in the chatroom list.
2. WHEN a `message` WebSocket event is received for a chatroom not currently open in the Dashboard, THE Dashboard SHALL set `has_unread: True` for that chatroom row and display the UnreadBadge.
3. WHEN a `message` WebSocket event is received for the currently open chatroom, THE Dashboard SHALL append the message to the message thread and SHALL NOT mark that chatroom as unread.
4. WHEN an `unread_update` WebSocket event is received, THE Dashboard SHALL update the unread indicator for the specified chatroom without requiring a page reload.
5. WHEN the Dashboard WebSocket connection is lost and re-established, THE Dashboard SHALL re-fetch the chatroom list to reconcile unread state.
