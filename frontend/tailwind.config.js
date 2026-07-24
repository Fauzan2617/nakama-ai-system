/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        nakama: {
          dark: '#1e293b',
          light: '#f8fafc',
          primary: '#3b82f6', // Warna biru profesional
        }
      }
    },
  },
  plugins: [],
}