---
name: SecureBank Executive System
colors:
  surface: '#f7fafc'
  surface-dim: '#d7dadc'
  surface-bright: '#f7fafc'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f1f4f6'
  surface-container: '#ebeef0'
  surface-container-high: '#e5e9eb'
  surface-container-highest: '#e0e3e5'
  on-surface: '#181c1e'
  on-surface-variant: '#43474e'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eef1f3'
  outline: '#74777f'
  outline-variant: '#c4c6cf'
  surface-tint: '#455f88'
  primary: '#002045'
  on-primary: '#ffffff'
  primary-container: '#1a365d'
  on-primary-container: '#86a0cd'
  inverse-primary: '#adc7f7'
  secondary: '#006a68'
  on-secondary: '#ffffff'
  secondary-container: '#91f0ed'
  on-secondary-container: '#006e6d'
  tertiary: '#172131'
  on-tertiary: '#ffffff'
  tertiary-container: '#2c3647'
  on-tertiary-container: '#959fb3'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d6e3ff'
  primary-fixed-dim: '#adc7f7'
  on-primary-fixed: '#001b3c'
  on-primary-fixed-variant: '#2d476f'
  secondary-fixed: '#94f2f0'
  secondary-fixed-dim: '#77d6d3'
  on-secondary-fixed: '#00201f'
  on-secondary-fixed-variant: '#00504e'
  tertiary-fixed: '#d9e3f9'
  tertiary-fixed-dim: '#bdc7dc'
  on-tertiary-fixed: '#121c2c'
  on-tertiary-fixed-variant: '#3d4759'
  background: '#f7fafc'
  on-background: '#181c1e'
  surface-variant: '#e0e3e5'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '600'
    lineHeight: 38px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  title-lg:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 8px
  container-max: 1280px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 40px
  stack-xs: 4px
  stack-sm: 12px
  stack-md: 24px
  stack-lg: 48px
---

## Brand & Style
The design system is engineered for a premium fintech experience that balances institutional stability with modern technological agility. The brand personality is authoritative yet accessible, targeting high-net-worth individuals and professionals who value precision and security.

The visual style is **Corporate / Modern** with a lean toward **Minimalism**. It prioritizes clarity through heavy whitespace and a restricted, high-contrast color palette. The UI should evoke a sense of "digital vault" reliability—uncluttered, fast, and deliberate. Every element must feel intentional, avoiding decorative flourishes in favor of functional elegance.

## Colors
This design system utilizes a high-contrast palette to establish a clear visual hierarchy and reinforce trust.

- **Primary (Deep Corporate Blue):** Used for core branding, primary actions, and navigational headers. It represents stability.
- **Accent (Vibrant Teal):** Reserved for growth indicators, success states, and key data callouts. It provides a modern "tech" pulse to the professional blue.
- **Neutrals:** The background uses an off-white (`#F7FAFC`) to reduce eye strain, while cards and containers use pure white (`#FFFFFF`) to pop against the canvas. 
- **Status Colors:** Use standard semantic reds for alerts and ambers for warnings, but keep them desaturated to maintain the premium aesthetic.

## Typography
The system relies exclusively on **Inter** to achieve a systematic, utilitarian aesthetic that remains highly legible at all sizes.

The type scale is generous, with significant contrast between display sizes and body copy. For financial data and metrics, use `tabular-nums` (monospaced numbers) to ensure columns of figures align perfectly. Headlines should utilize tighter letter spacing to feel more "locked-in" and professional. Labels used for metadata or category headers should be semi-bold to maintain hierarchy without needing excessive size.

## Layout & Spacing
This design system follows a **Fixed Grid** model for desktop to maintain a premium, editorial feel, switching to a fluid model for mobile devices.

- **Grid:** A 12-column grid is used for desktop (1280px max-width). Metric cards typically span 3 or 4 columns.
- **Rhythm:** An 8px base unit governs all spatial relationships. 
- **Breakpoints:**
  - **Mobile:** < 600px (Single column, 16px side margins).
  - **Tablet:** 600px - 1024px (8-column grid, fluid).
  - **Desktop:** > 1024px (12-column grid, centered).
- **Whitespace:** Use "generous" vertical stacking (`stack-lg`) between major sections to allow the data to breathe and prevent the interface from feeling "crowded," which is a common failure in fintech.

## Elevation & Depth
Depth is communicated through **Tonal Layers** and **Ambient Shadows**. 

The background is a flat neutral. Primary content sits on pure white cards. To indicate elevation, use extremely soft, large-radius shadows with low opacity (4–6%) tinted with the primary blue (`#1A365D`) rather than pure black. This creates a "lifted" effect that feels integrated into the brand's color space.

Avoid heavy borders or harsh shadows. For interactive elements like input fields, use a subtle 1px border in a light slate gray, which transitions to the Vibrant Teal accent upon focus.

## Shapes
The shape language is **Soft**, utilizing a 0.25rem (4px) base radius. This creates a precise, architectural feel that is friendlier than sharp corners but more professional than fully rounded or pill-shaped designs.

- **Standard Elements:** (Buttons, Inputs) 4px radius.
- **Containers:** (Cards, Modals) 8px (Large) or 12px (Extra Large) radius to soften the larger surface areas.
- **Data Visualizations:** Chart bars and progress indicators should have slightly rounded caps to maintain consistency with the UI.

## Components
- **Buttons:** Primary buttons are solid Deep Corporate Blue with white text. High-contrast is key. Secondary buttons use a Teal outline. Both use a 4px radius and 16px horizontal padding.
- **Metric Cards:** These are the centerpiece. Use a white background, a `headline-sm` for the value, and a `label-sm` for the title. Include a small trend indicator (Teal for up, Red for down) in the top right.
- **Input Fields:** Use a 1px border in Slate Gray. On focus, the border thickens to 2px and changes to Teal, accompanied by a very light Teal outer glow (2px blur).
- **Lists:** Transaction lists should use `body-md` for the description and `tabular-nums` for the amount. Rows are separated by 1px light gray dividers, with 16px of vertical padding per row.
- **Chips:** Small, 4px rounded tags used for transaction categories (e.g., "Food", "Transfer"). Use desaturated versions of the accent colors for the background with darker text for legibility.
- **Navigation:** A clean left-hand sidebar on desktop using the Deep Corporate Blue for the active state indicator—a simple 4px vertical bar on the left edge of the active link.