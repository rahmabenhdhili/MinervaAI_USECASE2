/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        'de-york': '#88c695',
        'pixie-green': '#b2d0ab',
        'foam': '#f5fefb',
        'viridian': '#3f8872',
        'shadow-green': '#9bc8bb',
        'silver-tree': '#51ae93',
        'moss-green': '#b6d89c',
        'dinero': {
          50: '#f5fefb',
          100: '#b2d0ab',
          200: '#9bc8bb',
          300: '#88c695',
          400: '#51ae93',
          500: '#3f8872',
          600: '#2d6352',
        }
      }
    },
  },
  plugins: [],
}
