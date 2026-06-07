/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', 'sans-serif'],
      },
      colors: {
        surface: {
          DEFAULT: '#18181b',
          elevated: '#111114',
          hover: '#1f1f23',
          active: '#27272a',
        },
        border: {
          DEFAULT: '#2e2e33',
          light: '#3f3f46',
        },
        accent: {
          DEFAULT: '#6366f1',
          hover: '#818cf8',
          soft: 'rgba(99, 102, 241, 0.12)',
        },
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease',
        'slide-up': 'slideUp 0.25s ease',
      },
      keyframes: {
        fadeIn: {
          from: { opacity: '0', transform: 'translateY(6px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(12px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
