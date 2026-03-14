# Implementation Plan: Widget Header Branding

## Overview

Additive changes across four files: extend the `WidgetConfig` type, parse new data attributes in `main.tsx`, rewrite the `Header` component to render branding with fallbacks, and update `ChatPanel` to pass the new props.

## Tasks

- [x] 1. Extend WidgetConfig interface with branding fields
  - Add optional `appName?: string`, `appDescription?: string`, `appLogoUrl?: string` to `WidgetConfig` in `widget-new/src/types/index.ts`
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 2. Update Config_Parser to read new data attributes
  - [x] 2.1 Add branding attribute reads in the `currentScript` branch of `main.tsx`
    - Read `data-app-name`, `data-app-description`, `data-app-logo-url` alongside existing attributes
    - _Requirements: 1.1, 2.1, 3.1, 4.2, 4.3, 5.4_

  - [ ]* 2.2 Write property test for Config_Parser branding mapping
    - **Property 1: Parser maps branding attributes to WidgetConfig**
    - **Validates: Requirements 1.1, 1.2, 2.1, 2.2, 3.1, 3.2**
    - Generate random strings for `appName`, `appDescription`, `appLogoUrl`; assert parsed `WidgetConfig` fields match


- [x] 3. Rewrite Header component with branding support
  - [x] 3.1 Update `HeaderProps` interface and component implementation in `widget-new/src/components/Header.tsx`
    - Remove `agentName`, `agentRole`, `isOnline`, `title` props
    - Add `appName?`, `appDescription?`, `appLogoUrl?` props
    - Render logo `<img>` (32×32, `object-fit: contain`) when `appLogoUrl` is set; hide logo area otherwise (no dot)
    - Render `appName` as title or fall back to static "Ch8r"
    - Render `appDescription` as subtitle or fall back to `Powered by <a href="https://ch8r.com">Ch8r</a>`
    - Attach `onError` handler to `<img>` that sets `display: none` on the element
    - _Requirements: 1.3, 1.4, 2.3, 2.4, 3.3, 3.4, 3.5, 3.6, 4.1_

  - [ ]* 3.2 Write property test for Header branding rendering
    - **Property 2: Header renders provided branding values**
    - **Validates: Requirements 1.3, 1.4, 2.3, 2.4, 4.1**
    - Generate arbitrary `appName`/`appDescription` (including `undefined`); assert rendered output contains correct title and subtitle text

  - [ ]* 3.3 Write property test for Header logo rendering
    - **Property 3: Header renders logo with correct attributes**
    - **Validates: Requirements 3.3, 3.4, 3.5**
    - Generate random `appLogoUrl` strings; assert `<img>` has correct `src`, `width`, `height`, `object-fit`; assert no `<img>` and no dot when `appLogoUrl` is `undefined`

  - [ ]* 3.4 Write unit tests for Header edge cases
    - Backward compatibility: render with no branding props; assert title is "Ch8r", subtitle contains `<a href="https://ch8r.com">` (Requirement 4.1)
    - Logo error handling: simulate `onError` on `<img>`; assert element has `display: none` (Requirement 3.6)
    - Fallback link: render with no `appDescription`; assert subtitle contains `<a href="https://ch8r.com">` (Requirement 2.4)

- [x] 4. Checkpoint — ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Update ChatPanel to pass branding props to Header
  - [x] 5.1 Update `Header` usage in `widget-new/src/components/ChatPanel.tsx`
    - Pass `appName`, `appDescription`, `appLogoUrl` from `config.value` to `<Header>`
    - Remove `agentName`, `agentRole`, `agentOnline`/`isOnline`, and `title` from the `<Header>` call
    - _Requirements: 1.3, 2.3, 3.3, 4.3_

- [x] 6. Final checkpoint — ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Property tests use **fast-check** with a minimum of 100 iterations each
- Each property test must include a comment: `// Feature: widget-header-branding, Property N: <property text>`
- The `window.Ch8rWidgetConfig` branch in `main.tsx` picks up the new fields automatically once the type is updated — no extra code needed there
