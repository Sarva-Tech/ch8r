# Design Document: Widget Header Branding

## Overview

This feature adds configurable branding to the embeddable chat widget header. Embedding sites supply an app name, description, and logo URL via `data-*` attributes on the script tag or via `window.Ch8rWidgetConfig`. The `Header` component is updated to render these values, replacing the online/offline dot with a company logo image (or hiding that area entirely when no logo is provided), and showing the app name and description with static fallbacks.

The change is purely additive: no existing fields are removed or renamed, and widgets without the new attributes continue to render identically to today.

---

## Architecture

The feature touches three layers in a straight top-down data flow:

```
window.Ch8rWidgetConfig / <script data-*>
        │
        ▼
  main.tsx  (Config_Parser)
  reads new attributes → populates WidgetConfig
        │
        ▼
  signals.ts  (config signal)
  WidgetConfig stored in a Preact signal
        │
        ▼
  ChatPanel.tsx
  reads config signal, passes branding props to Header
        │
        ▼
  Header.tsx  (Header_Component)
  renders logo / name / description with fallbacks
```

No new signals, stores, or network calls are required. The existing `config` signal already carries `WidgetConfig` to every component that needs it.

---

## Components and Interfaces

### WidgetConfig (types/index.ts)

Three optional fields are added:

```ts
appName?: string;        // maps to data-app-name
appDescription?: string; // maps to data-app-description
appLogoUrl?: string;     // maps to data-app-logo-url
```

All three default to `undefined`, preserving backward compatibility.

### Config_Parser (main.tsx)

The existing `if (window.Ch8rWidgetConfig)` branch already spreads the whole object into `parsedConfig`, so `appName`, `appDescription`, and `appLogoUrl` are picked up automatically once the type is updated.

The `else if (currentScript)` branch needs three new attribute reads added alongside the existing ones:

```ts
appName:        currentScript.getAttribute('data-app-name')        ?? undefined,
appDescription: currentScript.getAttribute('data-app-description') ?? undefined,
appLogoUrl:     currentScript.getAttribute('data-app-logo-url')    ?? undefined,
```

### Header Component (components/Header.tsx)

The `HeaderProps` interface gains three new optional fields mirroring `WidgetConfig`:

```ts
interface HeaderProps {
  appName?:        string;
  appDescription?: string;
  appLogoUrl?:     string;
  onClose: () => void;
  // agentName, agentRole, isOnline, title are removed — no longer used
}
```

The existing `agentName`, `agentRole`, `isOnline`, and `title` props are superseded by the branding fields. `ChatPanel` will stop passing them.

Rendering logic:

| Slot | Condition | Output |
|---|---|---|
| Logo area | `appLogoUrl` set | `<img src={appLogoUrl} width="32" height="32" style="object-fit:contain" onError={hideOnError}/>` |
| Logo area | `appLogoUrl` not set | nothing rendered (no dot either) |
| Title | `appName` set | `<p>{appName}</p>` |
| Title | `appName` not set | `<p>Ch8r</p>` |
| Subtitle | `appDescription` set | `<p>{appDescription}</p>` |
| Subtitle | `appDescription` not set | `<p>Powered by <a href="https://ch8r.com">Ch8r</a></p>` |

The broken-image handler sets `display: none` on the `<img>` via an `onError` callback so no broken-image icon is shown.

### ChatPanel (components/ChatPanel.tsx)

Reads the three new fields from `config.value` and passes them to `Header`:

```tsx
<Header
  appName={config.value?.appName}
  appDescription={config.value?.appDescription}
  appLogoUrl={config.value?.appLogoUrl}
  onClose={onClose}
/>
```

The `agentName`, `agentRole`, `agentOnline`, and `title` variables that were previously passed to `Header` are no longer needed for the header (they may still be used elsewhere in `ChatPanel`).

---

## Data Models

### Updated WidgetConfig

```ts
export interface WidgetConfig {
  // existing required fields
  appUuid: string;
  token: string;
  // existing optional fields
  accentColor?: string;
  position?: 'bottom-right' | 'bottom-left';
  title?: string;
  launcherIconUrl?: string;
  aiGreeting?: string;
  apiBaseUrl?: string;
  userIdentifier?: string;
  // new branding fields
  appName?: string;
  appDescription?: string;
  appLogoUrl?: string;
}
```

No migration or persistence changes are needed — `WidgetConfig` is ephemeral (populated at script load time, held in a signal, never serialized to storage).

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Parser maps branding attributes to WidgetConfig

*For any* combination of `appName`, `appDescription`, and `appLogoUrl` string values provided either as `data-*` attributes on the script tag or as properties of `window.Ch8rWidgetConfig`, the resulting `WidgetConfig` object produced by the Config_Parser shall contain those exact values in the corresponding fields.

**Validates: Requirements 1.1, 1.2, 2.1, 2.2, 3.1, 3.2**

### Property 2: Header renders provided branding values

*For any* `WidgetConfig` where `appName` and/or `appDescription` are set, the Header component's rendered output shall contain `appName` as the primary title text and `appDescription` as the subtitle text. When either field is `undefined`, the output shall contain the static fallback ("Ch8r" for title; "Powered by Ch8r" with an anchor to `https://ch8r.com` for subtitle).

**Validates: Requirements 1.3, 1.4, 2.3, 2.4, 4.1**

### Property 3: Header renders logo with correct attributes

*For any* `WidgetConfig` where `appLogoUrl` is set, the Header component's rendered output shall contain an `<img>` element whose `src` equals `appLogoUrl`, with `width` and `height` of 32, and `object-fit: contain` applied. When `appLogoUrl` is `undefined`, the rendered output shall contain neither an `<img>` element nor the online/offline dot indicator in the logo slot.

**Validates: Requirements 3.3, 3.4, 3.5**

---

## Error Handling

### Logo load failure

When the `<img>` element fires an `onError` event (e.g. 404, CORS block, invalid URL), an inline handler sets `display: none` on the element. This prevents the browser's broken-image icon from appearing. No fallback image or retry logic is applied — the logo area simply becomes empty, which is the same visual state as when no logo URL is provided.

### Missing required config

The existing guard in `main.tsx` (`if (!parsedConfig?.appUuid || !parsedConfig?.token)`) already handles the case where required fields are absent. The new branding fields are all optional and never trigger this guard.

### Invalid URL for appLogoUrl

No URL validation is performed at parse time. The browser handles the load attempt; if it fails, the `onError` handler hides the element as described above.

---

## Testing Strategy

### Dual Testing Approach

Both unit tests and property-based tests are required. They are complementary:

- Unit tests cover specific examples, integration points, and error conditions.
- Property-based tests verify universal correctness across a wide range of generated inputs.

### Property-Based Testing

Use **fast-check** (already available in the JS/TS ecosystem) as the property-based testing library.

Each property test must run a minimum of **100 iterations**.

Each test must include a comment referencing the design property it validates, using the format:
`// Feature: widget-header-branding, Property N: <property text>`

| Design Property | Test Description |
|---|---|
| Property 1 | Generate random strings for appName, appDescription, appLogoUrl; assert parsed WidgetConfig fields match |
| Property 2 | Generate random HeaderProps with arbitrary appName/appDescription (including undefined); assert rendered output contains correct title and subtitle text |
| Property 3 | Generate random appLogoUrl strings; assert rendered img has correct src/width/height/style; generate undefined appLogoUrl; assert no img and no dot |

### Unit Tests

Unit tests should focus on:

- **Backward compatibility example** (Requirement 4.3): Parse a config with only `appUuid` and `token`; assert branding fields are `undefined` and the widget renders without errors.
- **Logo error handling example** (Requirement 3.6): Render Header with a valid `appLogoUrl`; simulate `onError` on the img; assert the element has `display: none`.
- **Fallback link example** (Requirement 2.4): Render Header with no `appDescription`; assert the subtitle contains an `<a>` with `href="https://ch8r.com"`.

Avoid duplicating coverage already provided by property tests (e.g. do not write separate unit tests for every combination of defined/undefined branding fields).
