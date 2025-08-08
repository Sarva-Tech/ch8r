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
      apiBaseUrl: process.env.API_BASE_URL || 'http://localhost:8000/api',
      NUXT_PUBLIC_KEY: process.env.NUXT_PUBLIC_KEY || ''
    },
  },
})
