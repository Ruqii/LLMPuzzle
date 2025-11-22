Hexagram Particle Interaction Demo

A Three.js-based interactive experience featuring falling text particles, a gravity-like black hole interaction, and dynamic generation of dual hexagrams (卦象) using particle formation.

This project is built for web browsers and supports PWA installation.

Features
1. Falling Text Rain

Continuous rain of characters (letters + Chinese characters)

GPU-accelerated rendering using Three.js

Adjustable density, speed, and text content

2. Black Hole Interaction

Activated when the user presses on the screen

Attracts nearby particles with gravitational force

Smooth breathing/pulsing animation while active

Gradually absorbs particles until a threshold is reached

3. Dynamic Hexagram Formation

When enough particles are absorbed, two hexagrams are generated

Each hexagram consists of six lines (阴爻 / 阳爻)

Particles are assigned into formation queues

Lines appear sequentially with smooth particle locking animation

Two hexagrams slide upward smoothly after completion (for displaying text below)

4. Fully Modular Architecture

Each system is contained in its own class:

ParticleSystem – rain & formation particles

BlackHole – interaction, position, breathing, expand animation

Hexagram – receiving particles, line formation, animation

App – orchestrates everything

5. PWA Support

manifest.json included

Icons included

Ready to add your own service worker

📁 Project Structure
Hex/
│
├─ src/
│   ├─ app.js              # Main application controller
│   ├─ blackhole.js        # Black hole logic + animation
│   ├─ hexagram.js         # Hexagram generation system
│   └─ particleSystem.js   # Falling text + particle formation
│
├─ index.html              # Entry point
└─  manifest.json           # PWA manifest

