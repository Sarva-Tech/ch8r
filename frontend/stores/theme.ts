import { defineStore } from 'pinia'
import { AVAILABLE_COLORS, DEFAULT_COLOR } from '~/lib/consts'

export const useThemeStore = defineStore('theme', {
  state: () => ({
    currentTheme: DEFAULT_COLOR.id,
  }),

  actions: {
    setTheme(themeColor: string) {
      this.currentTheme = themeColor
      localStorage.setItem('theme_config', JSON.stringify({ currentTheme: themeColor }))
      this.applyTheme()
    },

    fetchAndApplyTheme() {
      if (import.meta.client) {
        const saved = localStorage.getItem('theme_config')
        if (saved) {
          const config = JSON.parse(saved)
          this.currentTheme = config.currentTheme || DEFAULT_COLOR.id
        }
        this.applyTheme()
      }
    },

    applyTheme() {
      if (!import.meta.client) return

      const htmlEl = document.documentElement

      const allColors = AVAILABLE_COLORS.map(color => `theme-${color.id}`)
      htmlEl.classList.remove(...allColors)

      htmlEl.classList.add(`theme-${this.currentTheme}`)
    }
  },
})
