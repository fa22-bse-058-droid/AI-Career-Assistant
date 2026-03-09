/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#0A0F1E',
          secondary: '#0D1117',
          card: 'rgba(13, 17, 23, 0.8)',
          border: 'rgba(59, 130, 246, 0.2)',
        },
        accent: {
          blue: '#3B82F6',
          purple: '#8B5CF6',
          cyan: '#06B6D4',
          green: '#10B981',
          red: '#EF4444',
          orange: '#F59E0B',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      backdropBlur: {
        xs: '2px',
        DEFAULT: '8px',
        md: '16px',
      },
      animation: {
        'gradient-shift': 'gradient-shift 6s ease infinite',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'float': 'float 3s ease-in-out infinite',
        'scan': 'scan 2s linear infinite',
        'spin-slow': 'spin 8s linear infinite',
      },
      keyframes: {
        'gradient-shift': {
          '0%, 100%': { 'background-position': '0% 50%' },
          '50%': { 'background-position': '100% 50%' },
        },
        'pulse-glow': {
          '0%, 100%': { 'box-shadow': '0 0 5px rgba(59, 130, 246, 0.5)' },
          '50%': { 'box-shadow': '0 0 20px rgba(59, 130, 246, 1), 0 0 40px rgba(139, 92, 246, 0.5)' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        'scan': {
          '0%': { top: '0%' },
          '100%': { top: '100%' },
        },
      },
      boxShadow: {
        glow: '0 0 15px rgba(59, 130, 246, 0.5)',
        'glow-purple': '0 0 15px rgba(139, 92, 246, 0.5)',
        'glow-cyan': '0 0 15px rgba(6, 182, 212, 0.5)',
        glass: '0 8px 32px rgba(0, 0, 0, 0.37)',
      },
    },
  },
  plugins: [],
}
