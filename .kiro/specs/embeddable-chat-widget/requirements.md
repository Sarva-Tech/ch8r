# Requirements Document

## Introduction

The Ch8r embeddable chat widget is a self-contained, embeddable UI component that third-party websites can drop in with a single script tag. It provides three interaction modes: live chat with human agents, chat with specialized AI agents, and a structured support/feedback form. The widget is built with Preact for a minimal footprint and uses Shadow DOM for full CSS and DOM isolation from the host page.

## Glossary

- **Widget**: The embeddable Preact-based chat UI component delivered as a single JavaScript bundle
- **Host_Page**: The third-party website that embeds the Widget via a script tag
- **Shadow_DOM**: Browser-native encapsulation boundary that isolates the Widget's DOM and styles from the Host_Page
- **Launcher**: The floating button rendered on the Host_Page that opens and closes the Chat_Panel
- **Chat_Panel**: The expanded chat interface containing the conversation view and input controls
- **Human_Agent**: A live support representative with a name, role/position, and online status
- **AI_Agent**: A specialized automated agent (e.g. billing bot, technical support bot) powered by the backend LLM pipeline
- **Support_Form**: A structured form for submitting feedback or support requests without entering a live chat
- **Chatroom**: A persistent conversation session identified by a unique identifier stored in localStorage
- **Sender_Identifier**: An anonymous UUID persisted in localStorage that uniquely identifies the visitor across sessions
- **Widget_Token**: A short-lived or long-lived bearer token issued by the backend that authorizes the Widget to communicate with the API
- **App_UUID**: The unique identifier of the Ch8r application instance the Widget is configured for
- **WebSocket**: The persistent bidirectional connection used to receive real-time messages from agents
- **postMessage**: The browser API used for communication between the Widget iframe/Shadow DOM and the Host_Page

---

## Requirements

### Requirement 1: Widget Embedding and Isolation

**User Story:** As a website owner, I want to embed the chat widget on my site with a single script tag, so that my site's styles and scripts are never broken by the widget and vice versa.

#### Acceptance Criteria

1. THE Widget SHALL be deliverable as a single JavaScript bundle that a Host_Page can load via one `<script>` tag
2. THE Widget SHALL render all its UI inside a Shadow DOM root attached to a dedicated host element, so that Host_Page CSS cannot leak into the Widget and Widget CSS cannot leak into the Host_Page
3. WHEN the Widget bundle is loaded, THE Widget SHALL inject its own scoped styles exclusively within the Shadow DOM boundary
4. THE Widget SHALL NOT rely on any CSS classes, IDs, or global styles defined by the Host_Page
5. THE Widget SHALL NOT modify any existing DOM nodes outside its own Shadow DOM host element
6. WHEN the Widget is initialized, THE Widget SHALL accept configuration (App_UUID, Widget_Token, and optional theme overrides) via a global configuration object or data attributes on the script tag
7. IF the Widget_Token or App_UUID is missing at initialization, THEN THE Widget SHALL render in a disabled state and log a descriptive error to the browser console

---

### Requirement 2: Launcher Button

**User Story:** As a website visitor, I want a visible but unobtrusive launcher button, so that I can open the chat at any time without it disrupting my browsing.

#### Acceptance Criteria

1. THE Launcher SHALL be rendered as a fixed-position floating button in the bottom-right corner of the viewport by default
2. WHEN the Chat_Panel is closed, THE Launcher SHALL be visible and interactive
3. WHEN the Launcher is clicked, THE Widget SHALL open the Chat_Panel with an animated transition
4. WHEN the Chat_Panel is open, THE Launcher SHALL be hidden
5. WHERE a custom position (bottom-left, bottom-right) is provided in the configuration, THE Widget SHALL render the Launcher at the specified position
6. WHERE a custom accent color is provided in the configuration, THE Widget SHALL apply that color to the Launcher background

---

### Requirement 3: Chat Panel Layout and Navigation

**User Story:** As a website visitor, I want a clear, navigable chat panel, so that I can easily switch between talking to a human, an AI agent, or submitting a form.

#### Acceptance Criteria

1. THE Chat_Panel SHALL display a header containing the active agent's name, role/position, and online status indicator
2. THE Chat_Panel SHALL provide navigation controls that allow the visitor to switch between Human_Agent chat, AI_Agent chat, and the Support_Form
3. WHEN the visitor switches between modes, THE Widget SHALL preserve the conversation history for each mode independently within the current session
4. THE Chat_Panel SHALL display a close/minimize button that returns the Widget to the Launcher state
5. WHEN the close button is clicked, THE Widget SHALL animate the Chat_Panel closed and restore the Launcher

---

### Requirement 4: Human Agent Chat

**User Story:** As a website visitor, I want to chat with a live human agent, so that I can get personalized support for complex issues.

#### Acceptance Criteria

1. WHEN the Human_Agent chat mode is active, THE Chat_Panel SHALL display the assigned Human_Agent's name and position in the header
2. WHEN the Human_Agent is online, THE Chat_Panel SHALL display a green online status indicator next to the agent's name
3. WHEN the Human_Agent is offline, THE Chat_Panel SHALL display an offline indicator and a message informing the visitor that no agents are currently available
4. WHEN the visitor submits a message, THE Widget SHALL send the message to the backend API using the Chatroom's send-message endpoint with the Sender_Identifier and Chatroom identifier
5. WHEN a new Chatroom is created by the backend, THE Widget SHALL persist the returned Chatroom identifier in localStorage keyed by the Sender_Identifier
6. WHEN a message is received over the WebSocket connection, THE Widget SHALL append the message to the conversation view and scroll to the latest message
7. IF the API request to send a message fails, THEN THE Widget SHALL display an inline error message and allow the visitor to retry
8. THE Widget SHALL establish a WebSocket connection using the Sender_Identifier when the Human_Agent chat mode is opened
9. IF the WebSocket connection is lost, THEN THE Widget SHALL attempt to reconnect with exponential backoff up to 5 retries before displaying a connection error to the visitor

---

### Requirement 5: AI Agent Chat

**User Story:** As a website visitor, I want to chat with a specialized AI agent, so that I can get instant automated answers to common questions.

#### Acceptance Criteria

1. WHEN the AI_Agent chat mode is active, THE Chat_Panel SHALL display the AI_Agent's configured name and role in the header
2. WHEN the visitor submits a message in AI_Agent mode, THE Widget SHALL send the message to the backend API and display a typing indicator while awaiting the response
3. WHEN the AI_Agent response is received, THE Widget SHALL append the response to the conversation view and remove the typing indicator
4. IF the AI_Agent API request fails, THEN THE Widget SHALL display an inline error message indicating the AI is temporarily unavailable
5. THE Widget SHALL maintain a separate conversation history for AI_Agent chat, independent of the Human_Agent chat history
6. WHEN the visitor opens AI_Agent mode for the first time in a session, THE Widget SHALL display a configurable greeting message from the AI_Agent

---

### Requirement 6: Support / Feedback Form

**User Story:** As a website visitor, I want to submit a support request or feedback without entering a live chat, so that I can report issues asynchronously.

#### Acceptance Criteria

1. THE Support_Form SHALL include fields for: visitor name, email address, subject, and message body
2. WHEN the visitor submits the Support_Form, THE Widget SHALL validate that all required fields are non-empty and that the email field contains a valid email format before sending
3. IF validation fails, THEN THE Widget SHALL display field-level error messages adjacent to each invalid field
4. WHEN the Support_Form is successfully submitted, THE Widget SHALL display a confirmation message and reset the form
5. IF the Support_Form submission API request fails, THEN THE Widget SHALL display an error message and preserve the visitor's entered data so they can retry
6. THE Support_Form SHALL be keyboard-navigable and each field SHALL have an associated visible label

---

### Requirement 7: Persistent Session State

**User Story:** As a website visitor, I want my conversation history to persist across page reloads, so that I don't lose context when I navigate the site.

#### Acceptance Criteria

1. THE Widget SHALL generate a Sender_Identifier as a UUID on first load and persist it in localStorage under the key `ch8r_sender_identifier`
2. WHEN the Widget is loaded on a page where a Sender_Identifier already exists in localStorage, THE Widget SHALL reuse the existing Sender_Identifier
3. THE Widget SHALL persist the message history for each chat mode in localStorage keyed by the Sender_Identifier and mode
4. WHEN the Widget is opened after a page reload, THE Widget SHALL restore and display the persisted message history
5. THE Widget SHALL persist the active Chatroom identifier in localStorage so that returning visitors continue the same conversation thread

---

### Requirement 8: Theming and Customization

**User Story:** As a website owner, I want to customize the widget's appearance to match my brand, so that the widget feels native to my site.

#### Acceptance Criteria

1. THE Widget SHALL expose a configuration API that accepts an accent color (hex or CSS color string) applied to the Launcher, header, and primary action buttons
2. WHERE a custom widget title is provided in the configuration, THE Widget SHALL display that title in the Chat_Panel header
3. WHERE a custom launcher icon URL is provided in the configuration, THE Widget SHALL render that image inside the Launcher button
4. THE Widget SHALL apply all theme values as CSS custom properties scoped within the Shadow DOM so that Host_Page styles cannot override them

---

### Requirement 9: Accessibility

**User Story:** As a website visitor using assistive technology, I want the widget to be fully keyboard-navigable and screen-reader-friendly, so that I can use it without a mouse.

#### Acceptance Criteria

1. THE Launcher SHALL have a descriptive `aria-label` attribute
2. THE Chat_Panel SHALL trap keyboard focus within itself while it is open, and return focus to the Launcher when it is closed
3. WHEN a new message is appended to the conversation view, THE Widget SHALL announce the message content to screen readers using an ARIA live region
4. THE Support_Form SHALL associate each input field with a visible `<label>` element using matching `for` and `id` attributes
5. THE Widget SHALL support full keyboard navigation using Tab, Shift+Tab, Enter, and Escape keys
6. WHEN the Escape key is pressed while the Chat_Panel is open, THE Widget SHALL close the Chat_Panel

---

### Requirement 10: Performance and Bundle Size

**User Story:** As a website owner, I want the widget to load quickly and not degrade my site's performance, so that my visitors' experience is not impacted.

#### Acceptance Criteria

1. THE Widget bundle (JavaScript + inlined CSS) SHALL NOT exceed 100 KB gzipped
2. THE Widget SHALL defer all non-critical initialization (WebSocket connection, history loading) until the Chat_Panel is first opened by the visitor
3. THE Widget SHALL NOT block the Host_Page's main thread during initialization
4. WHEN the Widget bundle is loaded, THE Widget SHALL complete its initial render of the Launcher within 200ms on a standard broadband connection
