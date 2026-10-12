/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
        body: ['"DM Sans"', '"Noto Sans SC"', 'sans-serif'],
      },
      colors: {
        terminal: {
          bg: '#080a0d',
          panel: '#11151b',
          border: '#1a1f28',
          green: '#4a9d8f',
          amber: '#d4a034',
          blue: '#5b7a9a',
          red: '#c44b3c',
          muted: '#8a8578',
          text: '#e6e1d6',
        },
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-up': 'slideUp 0.3s ease-out',
        'fade-in': 'fadeIn 0.4s ease-out',
      },
      keyframes: {
        slideUp: {
          '0%': { transform: 'translateY(8px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
