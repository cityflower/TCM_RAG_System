/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 中医药主题绿色系
        tcm: {
          50:  '#f0f9f1',
          100: '#dcf1de',
          200: '#bbe3bf',
          300: '#8ecc96',
          400: '#5cae68',
          500: '#388e47',
          600: '#277338',
          700: '#205c2e',
          800: '#1c4a27',
          900: '#193d22',
          950: '#0b2212',
        },
        herb: {
          light: '#e8f5e9',
          mid:   '#a5d6a7',
          main:  '#4caf50',
          dark:  '#2e7d32',
        }
      },
      fontFamily: {
        sans: ['Inter', 'Noto Sans SC', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'blink': 'blink 1s step-end infinite',
        'pulse-dot': 'pulseDot 1.4s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
        pulseDot: {
          '0%, 80%, 100%': { transform: 'scale(0)', opacity: '0.5' },
          '40%': { transform: 'scale(1)', opacity: '1' },
        }
      }
    },
  },
  plugins: [],
}
