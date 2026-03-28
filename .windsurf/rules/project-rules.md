---
trigger: always_on
description: Backend-specific development rules for Django application
globs: 
---

# ch8r Development Guidelines

ch8r is a self-hosted AI customer service automation engine. It has three parts: **backend** (Python/Django), **frontend** (Vue/Nuxt/Shadcn/Tailwind), and **widget** (Preact/Tailwind).

## Core Principles

- Prioritize long-term maintainability, consistency, and scalability
- Reuse existing code; avoid duplication
- Apply SOLID principles and design patterns where genuinely appropriate
- Do not over-engineer

---

## Backend

**Stack:** Python, Django
**Root directory:** `backend/`

### Canonical Reference Files

Before writing any backend code, read and match the patterns in these files:

| Layer | Reference File |
|---|---|
| Models | `backend/core/models/ai_provider.py` or `backend/models/app_ai_provider.py` |
| Serializers | `backend/core/serializers/ai_provider.py` or `backend/serializers/app_ai_provider.py` |
| Views | `backend/core/views/ai_provider.py` or `backend/views/app_ai_provider.py` |

All new models, serializers, and views **must follow the structure, naming conventions, and patterns** established in the `ai_provider` / `app_ai_provider` reference files. Do not deviate without strong justification.

### Tests

**Test directory:** `backend/core/tests/`
**Reference test files:** `tests/test_ai_provider.py`, `tests/test_app_ai_provider.py`

Every new feature must include tests covering:

1. Authenticated user can **create** the resource
2. The creating user can **view, update, and delete** their own resource
3. A different user **cannot view, update, or delete** another user's resource

Match the style, structure, and assertions from the reference test files exactly.

---

## Frontend

**Stack:** Vue 3, Nuxt, Shadcn Vue, Tailwind CSS
**Root directory:** `frontend/`

### Canonical Reference Files

Before writing any frontend code, read and match the patterns in:

- **Page:** `frontend/pages/settings/ai-providers.vue`
- **Components:** `frontend/components/AIProvider/`
- **Stores:** `frontend/stores/aiProvider.ts`, `frontend/stores/appAIProvider.ts`

### Rules

- Always use `<script setup lang="ts">`
- Always use semantic Tailwind color tokens: `bg-primary`, `text-secondary`, `bg-accent/10`, etc. — never raw colors
- All state management goes through a Pinia store; follow the `aiProvider.ts` / `appAIProvider.ts` store structure for any new feature

---

## Widget

**Stack:** Preact, Tailwind CSS
**Root directory:** `widget-new/`

### Rules

- Always use semantic Tailwind color tokens (same convention as frontend)
- Where the widget mirrors a frontend UI element, keep the UX and visual design consistent with the frontend equivalent
- Prioritize maintainability and consistency over novelty

---

## Quick Reference: Where to Look First

| Task | Look here first |
|---|---|
| New Django model | `backend/core/models/ai_provider.py` |
| New Django view | `backend/core/views/ai_provider.py` |
| New serializer | `backend/core/serializers/ai_provider.py` |
| New backend tests | `backend/core/tests/test_ai_provider.py` |
| New Vue page | `frontend/pages/settings/ai-providers.vue` |
| New Vue component | `frontend/components/AIProvider/` |
| New Pinia store | `frontend/stores/aiProvider.ts` |
| New widget UI | Match frontend equivalent; use semantic colors |