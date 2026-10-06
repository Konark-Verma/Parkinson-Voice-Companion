/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canva: {
          teal: "#1B7B75",         // Deep clinical teal from Canva template
          tealDark: "#125450",     // Dark teal text / headers
          mint: "#2DD4BF",         // Bright mint teal for pill cards
          mintMedium: "#38B2AC",   // Accent medium mint
          mintLight: "#E6F7F5",    // Soft mint background fill
          mintSoft: "#EDFAF7",     // Card surface soft background
          charcoal: "#1C2526",     // Dark charcoal heading text
          cream: "#F4F3EF",        // Warm off-white background
          creamLight: "#F8F9FA",
        },
        parkinson: {
          primary: "#1B7B75",      // Clinical Teal
          secondary: "#38B2AC",    // Calming Mint
          accent: "#D97706",       // High-visibility Amber
          success: "#059669",      // High-contrast Emerald
          danger: "#DC2626",       // Alert Red
          surface: "#F4F3EF",      // Canva warm off-white
          card: "#FFFFFF",
          text: "#1C2526"          // High-contrast dark charcoal
        }
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      fontSize: {
        'touch-title': ['2rem', { lineHeight: '2.5rem', fontWeight: '700' }],
        'touch-body': ['1.25rem', { lineHeight: '1.75rem' }],
        'touch-btn': ['1.35rem', { lineHeight: '1.85rem', fontWeight: '600' }]
      },
      minHeight: {
        'touch': '56px',
        'touch-lg': '72px'
      },
      borderRadius: {
        'canva-pill': '50px',
        'canva-card': '24px',
      }
    },
  },
  plugins: [],
}
