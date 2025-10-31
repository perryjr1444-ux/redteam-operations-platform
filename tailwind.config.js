/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./templates/**/*.html",
    "./frontend/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Military C2 Color Palette
        tactical: {
          bg: '#0a0f14',
          surface: '#111921',
          card: '#1a2332',
          border: '#2a3f5f',
          text: '#c9d1d9',
          muted: '#8b949e',
        },
        military: {
          green: {
            DEFAULT: '#4caf50',
            dark: '#2e7d32',
            light: '#81c784',
          },
          amber: {
            DEFAULT: '#ffc107',
            dark: '#ffa000',
            light: '#ffd54f',
          },
          red: {
            DEFAULT: '#f44336',
            dark: '#c62828',
            light: '#e57373',
          },
        },
        status: {
          operational: '#4caf50',
          online: '#4caf50',
          active: '#ffc107',
          warning: '#ffc107',
          critical: '#f44336',
          offline: '#607d8b',
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Rajdhani', 'Orbitron', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'scan': 'scan 2s linear infinite',
        'blink': 'blink 1s step-end infinite',
      },
      keyframes: {
        scan: {
          '0%, 100%': { transform: 'translateY(-100%)' },
          '50%': { transform: 'translateY(100%)' },
        },
        blink: {
          '0%, 50%': { opacity: 1 },
          '51%, 100%': { opacity: 0 },
        }
      }
    },
  },
  plugins: [],
}
