/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        basketball: {
          orange: '#FF6B35',
          dark: '#1a1a1a',
          gray: '#2a2a2a',
        },
      },
    },
  },
  plugins: [],
}