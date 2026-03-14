import type { Config } from 'tailwindcss';
import forms from '@tailwindcss/forms';

export default {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'ch8r-accent': 'var(--ch8r-accent)',
        'ch8r-accent-fg': 'var(--ch8r-accent-fg)',
      },
      borderRadius: {
        'ch8r': 'var(--ch8r-radius)',
      },
      fontFamily: {
        'ch8r': 'var(--ch8r-font)',
      },
    },
  },
  plugins: [forms],
} satisfies Config;
