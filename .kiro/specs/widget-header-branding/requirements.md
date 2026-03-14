# Requirements Document

## Introduction

This feature adds configurable branding to the embeddable chat widget header. Embedding sites can supply an app name, app description, and company logo URL via data attributes on the script tag (or via `window.Ch8rWidgetConfig`). The company logo replaces the existing online/offline dot indicator. When no logo URL is provided, the logo area is hidden gracefully. When branding attributes are not supplied, the header falls back to static product defaults: "Ch8r" as the title and "Powered by Ch8r" (linking to https://ch8r.com) as the subtitle. The `agentName` and `agentRole` values from the backend are not used as header text fallbacks.

## Glossary

- **Widget**: The embeddable Preact-based chat widget loaded via a `<script>` tag.
- **Header**: The top bar of the Widget that displays branding and a close button.
- **WidgetConfig**: The configuration object populated from `window.Ch8rWidgetConfig` or script `data-*` attributes.
- **App_Name**: The human-readable name of the embedding application, supplied via `data-app-name` or `WidgetConfig.appName`.
- **App_Description**: A short subtitle for the embedding application, supplied via `data-app-description` or `WidgetConfig.appDescription`.
- **App_Logo_URL**: A URL pointing to the embedding company's logo image, supplied via `data-app-logo-url` or `WidgetConfig.appLogoUrl`.
- **Config_Parser**: The initialization logic in `main.tsx` that reads data attributes and `window.Ch8rWidgetConfig` into a `WidgetConfig` object.
- **Header_Component**: The `Header` Preact component in `widget-new/src/components/Header.tsx`.

---

## Requirements

### Requirement 1: App Name Configuration

**User Story:** As an embedding site developer, I want to set a custom app name via a data attribute, so that the widget header reflects my product's branding instead of the backend agent name.

#### Acceptance Criteria

1. WHEN `data-app-name` is present on the script tag, THE Config_Parser SHALL read its value and store it as `WidgetConfig.appName`.
2. WHEN `window.Ch8rWidgetConfig` contains an `appName` property, THE Config_Parser SHALL use that value as `WidgetConfig.appName`.
3. WHEN `WidgetConfig.appName` is set, THE Header_Component SHALL display `appName` as the primary title text in the header.
4. WHEN `WidgetConfig.appName` is not set, THE Header_Component SHALL fall back to displaying the static text "Ch8r" as the primary title text.

---

### Requirement 2: App Description Configuration

**User Story:** As an embedding site developer, I want to set a custom app description via a data attribute, so that the widget header shows a relevant subtitle for my product.

#### Acceptance Criteria

1. WHEN `data-app-description` is present on the script tag, THE Config_Parser SHALL read its value and store it as `WidgetConfig.appDescription`.
2. WHEN `window.Ch8rWidgetConfig` contains an `appDescription` property, THE Config_Parser SHALL use that value as `WidgetConfig.appDescription`.
3. WHEN `WidgetConfig.appDescription` is set, THE Header_Component SHALL display `appDescription` as the subtitle text in the header.
4. WHEN `WidgetConfig.appDescription` is not set, THE Header_Component SHALL fall back to displaying the static text "Powered by Ch8r" as the subtitle text, where "Ch8r" is rendered as a hyperlink to `https://ch8r.com`.

---

### Requirement 3: Company Logo Configuration

**User Story:** As an embedding site developer, I want to display my company logo in the widget header, so that users immediately recognize the brand context of the chat.

#### Acceptance Criteria

1. WHEN `data-app-logo-url` is present on the script tag, THE Config_Parser SHALL read its value and store it as `WidgetConfig.appLogoUrl`.
2. WHEN `window.Ch8rWidgetConfig` contains an `appLogoUrl` property, THE Config_Parser SHALL use that value as `WidgetConfig.appLogoUrl`.
3. WHEN `WidgetConfig.appLogoUrl` is set, THE Header_Component SHALL render an `<img>` element using `appLogoUrl` as the `src` in the position previously occupied by the online/offline dot indicator.
4. WHEN `WidgetConfig.appLogoUrl` is set, THE Header_Component SHALL render the logo image with a fixed width of 32px and a fixed height of 32px, with `object-fit: contain` applied.
5. WHEN `WidgetConfig.appLogoUrl` is not set, THE Header_Component SHALL hide the logo area and SHALL NOT render the online/offline dot indicator.
6. IF the logo image fails to load, THEN THE Header_Component SHALL hide the broken image element so no broken-image icon is displayed to the user.

---

### Requirement 4: Backward Compatibility

**User Story:** As an existing embedding site developer, I want my current widget integration to continue working without changes, so that I do not need to update my script tag when this feature is deployed.

#### Acceptance Criteria

1. WHEN neither `data-app-name`, `data-app-description`, nor `data-app-logo-url` are provided, THE Widget SHALL render the header using the static defaults: "Ch8r" as the title, "Powered by Ch8r" (linking to `https://ch8r.com`) as the subtitle, and no logo or online/offline dot indicator.
2. THE Config_Parser SHALL treat `appName`, `appDescription`, and `appLogoUrl` as optional fields in `WidgetConfig`, with `undefined` as the default value for each.
3. WHEN `data-app-uuid` and `data-token` are present but the new branding attributes are absent, THE Widget SHALL initialize and render without errors.

---

### Requirement 5: WidgetConfig Type Integrity

**User Story:** As a widget developer, I want the `WidgetConfig` TypeScript type to include the new branding fields, so that integrations using `window.Ch8rWidgetConfig` benefit from type safety.

#### Acceptance Criteria

1. THE `WidgetConfig` interface SHALL include an optional `appName` field of type `string`.
2. THE `WidgetConfig` interface SHALL include an optional `appDescription` field of type `string`.
3. THE `WidgetConfig` interface SHALL include an optional `appLogoUrl` field of type `string`.
4. WHEN the `WidgetConfig` interface is updated, THE Config_Parser SHALL compile without type errors against the updated interface.
