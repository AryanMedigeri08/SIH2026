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
        // Institutional Credit System Tokens (Rich, High Contrast, Expressive)
        sovereign: {
          950: '#041523',
          900: '#07243a',
          800: '#0b3b60',
          700: '#0e4c7d',
          600: '#1d639b',
          500: '#257cbd',
          400: '#38bdf8',
          300: '#7dd3fc',
          200: '#bae6fd',
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
          cyan: '#06b6d4',
          indigo: '#4338ca',
          emerald: '#059669',
          amber: '#d97706',
          rose: '#e11d48',
          purple: '#7c3aed',
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
        card: '0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.04)',
        'card-hover': '0 10px 25px -5px rgb(11 59 96 / 0.10), 0 8px 10px -6px rgb(11 59 96 / 0.05)',
        'card-elevated': '0 12px 30px -8px rgb(0 0 0 / 0.12), 0 4px 12px -2px rgb(0 0 0 / 0.06)',
        glow: '0 4px 20px 0 rgba(11, 59, 96, 0.18)',
        'glow-cyan': '0 4px 16px 0 rgba(2, 132, 199, 0.22)',
        'glow-emerald': '0 4px 16px 0 rgba(5, 150, 105, 0.20)',
        'glow-amber': '0 4px 16px 0 rgba(217, 119, 6, 0.20)',
        'glow-rose': '0 4px 16px 0 rgba(225, 29, 72, 0.20)',
        'pill-active': '0 2px 8px 0 rgba(11, 59, 96, 0.25)',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-mesh': 'radial-gradient(at 0% 0%, rgba(11, 59, 96, 0.06) 0px, transparent 50%), radial-gradient(at 100% 0%, rgba(2, 132, 199, 0.05) 0px, transparent 50%), radial-gradient(at 50% 100%, rgba(5, 150, 105, 0.03) 0px, transparent 50%)',
      }
    },
  },
  plugins: [],
}
