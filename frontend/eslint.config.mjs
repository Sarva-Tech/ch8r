// @ts-check
import { createConfigForNuxt } from '@nuxt/eslint-config/flat'

export default createConfigForNuxt({
  features: {
    stylistic: true,
  },
}).append({
  rules: {
    '@stylistic/comma-dangle': 'off',
    '@stylistic/brace-style': 'off',
  },
})
