/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        custom: {
          black: '#000000e6',
          gray: '#666',
          bg: '#f7fafc',
          blue: '#004370'
        }
      },
      fontFamily: {
        sans: ['sans-serif']
      }
    },
  },
  plugins: [],
}
