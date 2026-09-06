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
        dark: {
          950: '#07090E',
          900: '#0B0F19',
          850: '#0F1626',
          800: '#141D30',
          750: '#1B2640',
          700: '#233252',
          600: '#334770',
        },
        accent: {
          primary: '#3B82F6',   // Electric Blue
          hover: '#2563EB',
          muted: '#1D4ED8',
          subtle: '#1E3A8A',
        },
        verdict: {
          supports: '#10B981',      // Emerald green
          supportsBg: '#064E3B',
          supportsBorder: '#059669',
          refutes: '#EF4444',       // Crimson red
          refutesBg: '#7F1D1D',
          refutesBorder: '#DC2626',
          insufficient: '#F59E0B',  // Amber
          insufficientBg: '#78350F',
          insufficientBorder: '#D97706',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        'glow-blue': '0 0 25px -5px rgba(59, 130, 246, 0.3)',
        'glow-green': '0 0 25px -5px rgba(16, 185, 129, 0.3)',
        'glow-red': '0 0 25px -5px rgba(239, 68, 68, 0.3)',
      },
      animation: {
        'pulse-subtle': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 8s linear infinite',
      }
    },
  },
  plugins: [],
}
