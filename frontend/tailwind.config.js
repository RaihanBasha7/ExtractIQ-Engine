/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#05070d',
          900: '#0a0e1a',
          850: '#0d1322',
          800: '#111827',
          700: '#1f2937',
        },
        brand: {
          blue: '#3B82F6',
          cyan: '#06B6D4',
          green: '#22C55E',
        },
        glass: {
          DEFAULT: 'rgba(255,255,255,0.04)',
          border: 'rgba(255,255,255,0.08)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 40px -10px rgba(59,130,246,0.45)',
        'glow-cyan': '0 0 40px -10px rgba(6,182,212,0.45)',
        'glow-green': '0 0 40px -10px rgba(34,197,94,0.45)',
        soft: '0 10px 40px -12px rgba(0,0,0,0.6)',
      },
      backgroundImage: {
        'grid-glow':
          'radial-gradient(circle at 50% 0%, rgba(59,130,246,0.15), transparent 60%)',
        'mesh':
          'radial-gradient(at 20% 20%, rgba(59,130,246,0.12) 0px, transparent 50%), radial-gradient(at 80% 0%, rgba(6,182,212,0.10) 0px, transparent 50%), radial-gradient(at 50% 100%, rgba(34,197,94,0.08) 0px, transparent 50%)',
      },
      animation: {
        'shimmer': 'shimmer 2s linear infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4,0,0.6,1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'spin-slow': 'spin 8s linear infinite',
      },
      transitionDuration: {
        '250': '250ms',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
        float: {
          '0%,100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
    },
  },
  plugins: [],
};
