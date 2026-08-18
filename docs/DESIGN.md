---
name: Industrial Integrity
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#393939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1b1c1c'
  surface-container: '#1f2020'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353535'
  on-surface: '#e4e2e1'
  on-surface-variant: '#e0c0b5'
  inverse-surface: '#e4e2e1'
  inverse-on-surface: '#303030'
  outline: '#a78a81'
  outline-variant: '#58423a'
  surface-tint: '#ffb59c'
  primary: '#ffb59c'
  on-primary: '#5c1a00'
  primary-container: '#b7410e'
  on-primary-container: '#ffe2d9'
  inverse-primary: '#a93702'
  secondary: '#c0c8cd'
  on-secondary: '#2a3136'
  secondary-container: '#424a4f'
  on-secondary-container: '#b2b9bf'
  tertiary: '#c2c6d2'
  on-tertiary: '#2c3139'
  tertiary-container: '#646872'
  on-tertiary-container: '#e4e8f4'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdbcf'
  primary-fixed-dim: '#ffb59c'
  on-primary-fixed: '#380c00'
  on-primary-fixed-variant: '#822800'
  secondary-fixed: '#dce4e9'
  secondary-fixed-dim: '#c0c8cd'
  on-secondary-fixed: '#151d21'
  on-secondary-fixed-variant: '#40484c'
  tertiary-fixed: '#dfe2ee'
  tertiary-fixed-dim: '#c2c6d2'
  on-tertiary-fixed: '#171c24'
  on-tertiary-fixed-variant: '#424750'
  background: '#131313'
  on-background: '#e4e2e1'
  surface-variant: '#353535'
typography:
  headline-xl:
    fontFamily: IBM Plex Sans
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: IBM Plex Sans
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: IBM Plex Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: IBM Plex Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
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
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 16px
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 14px
spacing:
  unit: 4px
  gutter: 16px
  margin-mobile: 16px
  margin-desktop: 32px
  container-max: 1440px
---

## Brand & Style
The design system is engineered for the heavy-duty world of welding and machine maintenance. It prioritizes reliability, structural strength, and technical precision. The visual language is inspired by industrial environments: steel workshops, blueprints, and high-performance machinery.

The style is a fusion of **Corporate Modern** and **Soft Brutalism**. It utilizes clean grid lines and sharp geometry to convey a sense of "built-to-last" engineering. Subtle metallic gradients and micro-textures provide a tactile, high-quality finish without sacrificing the functional clarity required for data-heavy management interfaces. The emotional response is one of absolute trust, safety, and professional competence.

## Colors
The palette is rooted in the materials of the trade. **Dark Iron (#2B2B2B)** serves as the primary canvas, providing a high-contrast, low-glare background suitable for industrial environments. **Steel Gray (#71797E)** and **Brushed Metal (#A5A9B4)** are used for structural elements, borders, and secondary surfaces to create depth through tonal layering.

**Rust Orange (#B7410E)** is the high-visibility accent color. It is used strategically for primary actions, critical status indicators, and highlights, echoing the heat of a weld or the importance of safety equipment. High-contrast white is reserved strictly for maximum readability of data and labels against the dark surfaces.

## Typography
The typography system uses a tiered technical approach. **IBM Plex Sans** is used for headlines to provide a structured, engineered feel with its unique terminals and technical curves. **Inter** handles the bulk of data and body text, chosen for its exceptional legibility in complex interfaces. 

For technical data, serial numbers, and machine specifications, **JetBrains Mono** is employed. The monospaced nature of the label font ensures that numerical data aligns perfectly in tables and technical readouts. High-weight headlines and uppercase labels create a clear information hierarchy that remains readable even in low-light or high-stress situations.

## Layout & Spacing
The layout follows a **Fixed Grid** philosophy with a rigorous 4px baseline shift. This "blueprint" precision ensures that all elements feel intentionally placed and structurally sound. 

On desktop, a 12-column grid is used with 16px gutters to maximize data density while maintaining scanability. Margins are generous at 32px to frame the content. On mobile devices, the system collapses to a 4-column grid with reduced margins. Elements should favor vertical stacking to maintain large tap targets, essential for users who may be operating in a mobile workshop environment.

## Elevation & Depth
Depth is communicated through **Tonal Layers and Bold Borders** rather than traditional soft shadows. This design system avoids "floating" elements, preferring a "bolted-down" look.

1.  **Base Layer:** Dark Iron (#2B2B2B) background.
2.  **Surface Layer:** Steel Gray (#71797E) for cards and containers, using a 1px solid border in Brushed Metal (#A5A9B4) to define edges.
3.  **Active Layer:** Elements that require interaction use a subtle vertical linear gradient (Light to Dark) to simulate a physical brushed-metal texture.

Instead of shadows, use "Inset" borders or 2px solid offsets to indicate depth and depression (e.g., when a button is pressed). This reinforces the heavy-duty, tactile nature of the UI.

## Shapes
The shape language is strictly **Sharp (0px roundedness)**. Every container, button, and input field features 90-degree corners to reflect the precision of metal cutting and machine fabrication. This lack of rounding emphasizes a serious, industrial-grade toolset. Structural integrity is visualised through thickness; use 1px or 2px borders consistently to frame content areas.

## Components
- **Buttons:** Primary buttons use a solid Rust Orange (#B7410E) fill with white uppercase JetBrains Mono text. Secondary buttons are "Ghost" style with a 1px Steel Gray border. All buttons have a hover state that increases the border thickness to 2px, simulating a mechanical engagement.
- **Input Fields:** Dark backgrounds with a 1px bottom-border only (Blueprint style) or a full 1px border. Focus states must use the Rust Orange color for the border and the caret.
- **Cards:** Sharp corners, Steel Gray background, with a subtle top-border highlight in Brushed Metal (#A5A9B4) to simulate light hitting a metal edge.
- **Lists & Tables:** High-density rows separated by 1px Dark Iron borders. Use JetBrains Mono for all numerical data within tables.
- **Status Chips:** Rectangular with no rounding. Use high-saturation colors (Safety Red, Caution Yellow, Success Green) but keep them within the industrial tonal range (slightly desaturated/darkened).
- **Maintenance Logs:** Use vertical "timeline" lines that look like structural beams to connect historical data points.