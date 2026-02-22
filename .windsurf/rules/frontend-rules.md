---
description: Frontend-specific development rules for Nuxt.js application
trigger: always_on
---

# Frontend Development Rules

## Nuxt.js Architecture

### Project Structure

```
frontend/
├── components/     # Vue components
├── pages/         # Page components (auto-routing)
├── layouts/       # Layout components
├── composables/   # Vue composables
├── stores/        # Pinia stores
├── middleware/    # Route middleware
├── utils/         # Utility functions
├── assets/        # Static assets
└── server/        # Server-side code
```

### Component Organization

- Group components by feature/domain
- Use PascalCase for component names
- Keep components focused and reusable
- Use index files for component exports

## Vue.js Development Standards

### Component Structure

- Use Composition API with `<script setup>` syntax
- Implement proper TypeScript interfaces
- Use reactive refs and computed properties
- Follow single responsibility principle

```vue
<template>
  <div class="component-container">
    <!-- Template content -->
  </div>
</template>

<script setup lang="ts">
interface Props {
  title: string
  items: Item[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  update: [value: string]
  delete: [id: number]
}>()

// Component logic
</script>

<style scoped>
/* Component styles */
</style>
```

### TypeScript Integration

- Use TypeScript for all new components
- Define proper interfaces for props and emits
- Use type-safe composables
- Implement proper error handling

### State Management with Pinia

- Use Pinia stores for global state
- Implement proper store organization
- Use composables for store access
- Keep stores focused and minimal

```typescript
// stores/example.ts
export const useExampleStore = defineStore('example', () => {
  const items = ref<Item[]>([])
  const loading = ref(false)

  const fetchItems = async () => {
    loading.value = true
    try {
      items.value = await api.getItems()
    } catch (error) {
      console.error('Failed to fetch items:', error)
    } finally {
      loading.value = false
    }
  }

  return { items, loading, fetchItems }
})
```

## UI/UX Development Rules

### Component Library Usage

- Use ShadCN Vue components as primary UI library
- Follow established design patterns
- Customize components through props, not CSS overrides
- Use Reka UI for complex component interactions

### Tailwind CSS Standards

- Use Tailwind utility classes for all styling
- Avoid custom CSS unless absolutely necessary
- Use responsive design prefixes (sm:, md:, lg:, xl:)
- Implement dark mode support

```vue
<template>
  <div class="p-4 bg-white dark:bg-gray-800 rounded-lg shadow-md">
    <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
      {{ title }}
    </h2>
  </div>
</template>
```

### Accessibility Requirements

- Implement proper ARIA labels and roles
- Ensure keyboard navigation support
- Use semantic HTML elements
- Test with screen readers

## API Integration Rules

### Composable Pattern

- Create composables for API interactions
- Implement proper error handling
- Use loading states and error states
- Cache responses when appropriate

```typescript
// composables/useApi.ts
export const useApi = () => {
  const loading = ref(false)
  const error = ref<string | null>(null)

  const call = async <T>(
    endpoint: string,
    options?: RequestInit,
  ): Promise<T | null> => {
    loading.value = true
    error.value = null

    try {
      const response = await $fetch<T>(endpoint, options)
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error'
      return null
    } finally {
      loading.value = false
    }
  }

  return { loading, error, call }
}
```

### Error Handling

- Implement global error handling
- Show user-friendly error messages
- Log errors for debugging
- Implement retry logic for failed requests

### Data Validation

- Use Zod for runtime validation
- Validate API responses
- Implement proper type guards
- Handle validation errors gracefully

## Performance Optimization

### Code Splitting

- Use dynamic imports for heavy components
- Implement route-based code splitting
- Lazy load images and assets
- Optimize bundle size

### Caching Strategy

- Use Nuxt's built-in caching
- Implement proper HTTP caching headers
- Cache API responses in composables
- Use service workers for offline support

### Rendering Optimization

- Use Vue's built-in optimizations
- Implement proper key attributes for lists
- Avoid unnecessary re-renders
- Use computed properties efficiently

## Security Implementation

### Client-Side Security

- Sanitize user inputs
- Implement XSS protection
- Use secure cookie practices
- Validate all user inputs

### API Security

- Use HTTPS for all API calls
- Implement proper authentication
- Store tokens securely
- Handle sensitive data carefully

<!-- ## Testing Requirements -->

<!-- ### Component Testing

- Test all components with Vue Test Utils
- Mock external dependencies
- Test user interactions
- Test error states -->

<!-- ### E2E Testing

- Use Playwright for E2E tests
- Test critical user flows
- Test responsive design
- Test accessibility

### Unit Testing

- Test composables and utilities
- Test store functionality
- Test API integration
- Achieve minimum 80% coverage -->

## Development Workflow

### Code Quality

- Use ESLint for code linting
- Use Prettier for code formatting
- Follow Vue.js style guide
- Implement pre-commit hooks

### Build Process

- Use Nuxt's build optimization
- Implement proper environment configuration
- Use CI/CD for automated testing
- Monitor build performance

### Debugging

- Use Vue DevTools for debugging
- Implement proper logging
- Use browser developer tools
- Test in multiple browsers

<!-- ## Internationalization -->

<!-- ### i18n Implementation

- Use Nuxt's built-in i18n support
- Implement proper translation keys
- Support multiple languages
- Test RTL languages if needed -->

### Date/Time Formatting

- Use dayjs for date manipulation
- Implement proper timezone handling
- Format dates according to locale
- Handle relative time display

## Animation and Transitions

### Vue Transitions

- Use Vue's transition components
- Implement smooth animations
- Respect user preferences (prefers-reduced-motion)
- Optimize animation performance

### Loading States

- Implement skeleton loaders
- Use progress indicators
- Show loading states for async operations
- Handle loading errors gracefully
