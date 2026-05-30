/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          primary:   '#0B0C0E',
          secondary: '#111316',
          tertiary:  '#181A1D',
          elevated:  '#1E2025',
          card:      '#14161A',
        },
        border: {
          subtle:  'rgba(255,255,255,0.06)',
          DEFAULT: 'rgba(255,255,255,0.10)',
          hover:   'rgba(255,255,255,0.18)',
          active:  'rgba(255,255,255,0.24)',
        },
        accent: {
          1: '#3B82F6',
          2: '#06B6D4',
          3: '#8B5CF6',
        },
        text: {
          primary:   '#EDEEF0',
          secondary: '#949699',
          tertiary:  '#636669',
          disabled:  '#3D3F44',
        },
        slate: {
          950: '#0f1115',
        },
      },
      fontFamily: {
        display: ['"Plus Jakarta Sans"', 'sans-serif'],
        mono:    ['"JetBrains Mono"', 'monospace'],
      },
      borderRadius: {
        chat:    '18px',
        'chat-l': '4px 18px 18px 18px',
        'chat-r': '18px 18px 4px 18px',
      },
      boxShadow: {
        glow:   '0 0 20px rgba(59,130,246,0.15)',
        'glow-lg': '0 0 40px rgba(59,130,246,0.25)',
        card:   '0 1px 3px rgba(0,0,0,0.3)',
        elevated: '0 8px 32px rgba(0,0,0,0.5)',
      },
      animation: {
        shimmer:   'shimmer 2s ease-in-out infinite',
        drift:     'drift 30s ease-in-out infinite alternate',
        'fade-in': 'fadeIn 0.25s cubic-bezier(0.22,1,0.36,1) both',
        'slide-up': 'slideUp 0.35s cubic-bezier(0.34,1.56,0.64,1) both',
        'scale-in': 'scaleIn 0.25s cubic-bezier(0.34,1.56,0.64,1) both',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
      },
      keyframes: {
        shimmer: {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        drift: {
          '0%':   { transform: 'translate(0, 0) scale(1)' },
          '100%': { transform: 'translate(2%, 1%) scale(1.02)' },
        },
        fadeIn: {
          from: { opacity: '0' },
          to:   { opacity: '1' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(12px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          from: { opacity: '0', transform: 'scale(0.95)' },
          to:   { opacity: '1', transform: 'scale(1)' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 8px rgba(59,130,246,0.1)' },
          '50%':      { boxShadow: '0 0 20px rgba(59,130,246,0.25)' },
        },
      },
    },
  },
  plugins: [],
};
