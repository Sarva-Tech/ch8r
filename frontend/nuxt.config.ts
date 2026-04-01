import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  compatibilityDate: '2025-05-15',
  devtools: { enabled: true },
  ssr: false,
  css: ['~/assets/css/main.css'],

  modules: [
    '@nuxt/eslint',
    '@nuxt/fonts',
    '@nuxt/icon',
    '@nuxt/image',
    'shadcn-nuxt',
    '@pinia/nuxt',
    'dayjs-nuxt',
    '@nuxtjs/color-mode'
  ],

  shadcn: {
    prefix: '',
    componentDir: './components/ui',
  },

  dayjs: {
    plugins: ['relativeTime'],
  },

  colorMode: {
    classSuffix: ''
  },

  vite: {
    plugins: [tailwindcss()],
  },

  runtimeConfig: {
    public: {
      domain: process.env.DOMAIN || 'localhost:8002',
      apiBaseUrl: process.env.API_BASE_URL || 'http://localhost:8002/api',
      NUXT_PUBLIC_KEY: process.env.NUXT_PUBLIC_KEY || '',
      widgetApiBaseUrl: process.env.WIDGET_API_BASE_URL || 'http://localhost:8002',
      widgetAppUuid: process.env.WIDGET_APP_UUID || '',
      widgetToken: process.env.WIDGET_TOKEN || '',
      widgetAppName: process.env.WIDGET_APP_NAME || 'ch8r support',
      widgetAppDescription: process.env.WIDGET_APP_DESCRIPTION || "We're here to help",
      widgetAppLogoUrl: process.env.WIDGET_APP_LOGO_URL || 'http://localhost:3000/favicon.ico',
      widgetOffsetBottom: process.env.WIDGET_OFFSET_BOTTOM || '64',
      widgetTheme: process.env.WIDGET_THEME || 'blue',
    },
  },
})