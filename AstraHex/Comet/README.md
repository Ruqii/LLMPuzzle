# Comet Hexagram Animation

An interactive fullscreen animation featuring 6 concentric rings with orbiting comets that draw bright hexagram patterns.

## Features

- **Fullscreen PWA-compatible** - Works on mobile and desktop
- **6 concentric circular rings** - Each with one comet particle
- **Interactive animation states**:
  - **Idle**: Dim tracks visible, no comet movement
  - **Orbiting**: Press and hold to start all comets orbiting
  - **Revealing**: Release to watch comets draw their bright rings
    - Comets continue orbiting from 0° and "reveal" their rings as they move
    - Pattern `[1, 0, 1, 1, 0, 1]` determines each ring's final state:
      - `1` = Full circle (comet travels to 360°)
      - `0` = 45° gap (comet stops at 315°, leaving gap at 315°-360°)

## Visual Design

- **Dim tracks**: Always visible at `rgba(255, 255, 255, 0.08)`
- **Comets**: Bright white head with short fading tail
- **Revealed rings**: Bright white arcs (`arc(0 → revealAngle)`) drawn by comet heads
- **Render order**: Dim tracks → Comet tails & heads → Bright revealed arcs

## How to Use

### Desktop
1. Open `index.html` in a web browser
2. Click and hold to start the comets orbiting around their tracks
3. Release to watch comets reset to 0° and draw their bright rings
   - Rings 1, 3, 4, 6 will draw full circles (360°)
   - Rings 2, 5 will draw partial circles (stop at 315°)

### Mobile
1. Open `index.html` in a mobile browser
2. Tap and hold to start the comets orbiting
3. Release to watch the revealing animation

### As a PWA
1. Serve the directory using a local server (e.g., `python -m http.server 8000`)
2. Open in a browser and install as a PWA
3. Enjoy the fullscreen experience

## Files

- `index.html` - Main application with embedded CSS and JavaScript
- `manifest.json` - PWA configuration
- `README.md` - This file

## Customization

You can modify these variables in `index.html`:

```javascript
const NUM_RINGS = 6;                // Number of rings
const PATTERN = [1, 0, 1, 1, 0, 1]; // Hexagram pattern (1=full, 0=gap)
const baseRadius = 40;              // Starting radius
const radiusIncrement = 35;         // Space between rings
const orbitSpeed = 0.03;            // Speed during orbiting phase
const revealSpeed = 0.02;           // Speed during revealing phase
```

## Design

- **Background**: Black (`#000`)
- **Lines/Comets/Arcs**: White with varying opacity
- **Responsive**: Automatically adapts to screen size
- **Touch-optimized**: Prevents scrolling and context menus
