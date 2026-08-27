/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Institutional Credit System Tokens (Light-First, High Contrast)
        sovereign: {
          900: '#07243a',
          800: '#0b3b60',
          700: '#0e4c7d',
          600: '#1d639b',
          500: '#257cbd',
          100: '#e0f0fe',
          50: '#f0f7ff',
        },
        surface: {
          canvas: '#f8fafc',
          card: '#ffffff',
          inset: '#f1f5f9',
          muted: '#e2e8f0',
          border: '#e2e8f0',
          'border-strong': '#cbd5e1',
        },
        brand: {
          navy: '#0b3b60',
          blue: '#1e40af',
          sky: '#0284c7',
          cyan: '#0284c7',
          indigo: '#1e40af',
          emerald: '#059669',
          amber: '#d97706',
          rose: '#dc2626',
        },
        // Backward-compatibility token mappings for safety
        cyber: {
          dark: '#0f172a',
          surface: '#ffffff',
          card: '#ffffff',
          border: '#e2e8f0',
        }
      },
      fontFamily: {
        sans: ['Inter', 'Noto Sans Devanagari', 'Noto Sans Tamil', 'Noto Sans Telugu', 'Noto Sans Kannada', 'system-ui', 'sans-serif'],
        display: ['Outfit', 'Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        subtle: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        card: '0 1px 3px 0 rgb(0 0 0 / 0.07), 0 1px 2px -1px rgb(0 0 0 / 0.04)',
        'card-elevated': '0 4px 16px -2px rgb(0 0 0 / 0.08), 0 2px 4px -2px rgb(0 0 0 / 0.04)',
        glow: '0 4px 14px 0 rgba(11, 59, 96, 0.15)',
        'glow-cyan': '0 4px 14px 0 rgba(2, 132, 199, 0.15)',
        'glow-emerald': '0 4px 14px 0 rgba(5, 150, 105, 0.15)',
        'glow-rose': '0 4px 14px 0 rgba(220, 38, 38, 0.15)',
      }
    },
  },
  plugins: [],
}
