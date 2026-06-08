/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', 'sans-serif'],
      },
      colors: {
        canvas: '#09090b',
        surface: {
          DEFAULT: '#111114',
          elevated: '#18181b',
          hover: '#1f1f24',
          active: '#27272c',
        },
        border: {
          DEFAULT: '#2a2a30',
          light: '#3a3a42',
        },
        muted: '#71717a',
        accent: {
          DEFAULT: '#6366f1',
          hover: '#818cf8',
          soft: 'rgba(99, 102, 241, 0.14)',
        },
        brand: {
          300: '#a5b4fc',
          500: '#6366f1',
          700: '#4338ca',
        },
        success: '#34d399',
        warning: '#fbbf24',
        danger: '#f87171',
      },
      boxShadow: {
        panel: '0 0 0 1px rgba(255,255,255,0.04), 0 8px 32px rgba(0,0,0,0.35)',
        float: '0 12px 40px rgba(0,0,0,0.45)',
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
