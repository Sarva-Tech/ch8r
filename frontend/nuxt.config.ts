import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  compatibilityDate: '2025-05-15',
  devtools: { enabled: true },
  css: ['~/assets/css/main.css'],

  modules: [
    '@nuxt/eslint',
    '@nuxt/fonts',
    '@nuxt/icon',
    '@nuxt/image',
    'shadcn-nuxt',
    '@pinia/nuxt',
    'dayjs-nuxt',
  ],

  shadcn: {
    prefix: '',
    componentDir: './components/ui',
  },

  dayjs: {
    plugins: ['relativeTime'],
  },

  vite: {
    plugins: [tailwindcss()],
  },
   runtimeConfig: {
    public: {
      apiBaseUrl: process.env.API_BASE_URL || 'http://localhost:8000/api',
    },
  },
})
