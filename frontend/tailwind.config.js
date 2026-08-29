/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        parkinson: {
          primary: "#1E3A8A",      // Clinical Navy Blue
          secondary: "#0284C7",    // Calming Teal / Blue
          accent: "#D97706",       // High-visibility Amber
          success: "#059669",      // High-contrast Emerald
          danger: "#DC2626",       // Alert Red
          surface: "#F8FAFC",      // Off-white gentle background
          card: "#FFFFFF",
          text: "#0F172A"          // High-contrast deep slate
        }
      },
      fontSize: {
        'touch-title': ['2rem', { lineHeight: '2.5rem', fontWeight: '700' }],
        'touch-body': ['1.25rem', { lineHeight: '1.75rem' }],
        'touch-btn': ['1.35rem', { lineHeight: '1.85rem', fontWeight: '600' }]
      },
      minHeight: {
        'touch': '56px',
        'touch-lg': '72px'
      }
    },
  },
  plugins: [],
}
