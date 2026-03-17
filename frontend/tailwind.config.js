/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'slate': {
          850: '#17202f',
          900: '#0f172a',
        },
        'coral': {
          500: '#ff7f50',
          600: '#ff6347',
        }
      }
    }
  },
  plugins: [],
}