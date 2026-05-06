module.exports = {
  content: ["./src/**/*.{jsx,js,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        accent: '#8B5CF6',
        background: '#0a0a0b',
      },
      animation: {
        'gradient': 'gradientShift 30s ease infinite',
      },
      keyframes: {
        gradientShift: {
          '0%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
          '100%': { backgroundPosition: '0% 50%' },
        },
      },
    },
  },
  plugins: [],
}