// blackhole.js - Touch interaction + smooth expansion for hexagram

window.BlackHole = class BlackHole {
    constructor(scene, camera) {
        this.scene = scene;
        this.camera = camera;

        this.isActive = false;
        this.pulsing = false;    
        this.position = new THREE.Vector3();
        this.radius = 1;
        this.strength = 0.5;
        this.absorbedCount = 0;

        this.mesh = null;

        this.createVisual();
    }

    createVisual() {
        // Create radial ink-like gradient texture
        const canvas = document.createElement('canvas');
        canvas.width = 256;
        canvas.height = 256;
        const ctx = canvas.getContext('2d');

        const g = ctx.createRadialGradient(128, 128, 0, 128, 128, 128);
        g.addColorStop(0, 'rgba(0, 0, 0, 1)');
        g.addColorStop(0.25,'rgba(20, 20, 20, 0.8)');
        g.addColorStop(0.65,'rgba(80, 80, 80, 0.35)');
        g.addColorStop(1, 'rgba(120, 120, 120, 0)');

        ctx.fillStyle = g;
        ctx.fillRect(0,0,256,256);

        const texture = new THREE.CanvasTexture(canvas);
        texture.needsUpdate = true;

        const material = new THREE.SpriteMaterial({
            map: texture,
            transparent: true,
            opacity: 0,
            blending: THREE.AdditiveBlending
        });

        this.mesh = new THREE.Sprite(material);

        // Keep sprite centered
        this.mesh.center.set(0.5, 0.5);    // VERY IMPORTANT

        this.mesh.scale.set(0, 0, 1);
        this.scene.add(this.mesh);
    }


    activate(screenX, screenY) {
        // Convert screen coords → world coords
        const rect = this.camera.userData.containerRect;
        const x = (screenX / rect.width) * 2 - 1;
        const y = -(screenY / rect.height) * 2 + 1;

        const vector = new THREE.Vector3(x, y, 0.5);
        vector.unproject(this.camera);

        const dir = vector.sub(this.camera.position).normalize();
        const dist = -this.camera.position.z / dir.z;

        this.position.copy(this.camera.position).add(dir.multiplyScalar(dist));
        this.mesh.position.copy(this.position);

        this.isActive = true;
        this.absorbedCount = 0;

        this.pulsing = true;

        // Appear animation
        if (window.TWEEN) {
            new TWEEN.Tween(this.mesh.scale)
                .to({ x: 3, y: 3 }, 300)
                .easing(TWEEN.Easing.Elastic.Out)
                .start();

            new TWEEN.Tween(this.mesh.material)
                .to({ opacity: 0.85 }, 280)
                .start();
        }
    }


    update(screenX, screenY) {
        if (!this.isActive) return;

        // Move with pointer
        const rect = this.camera.userData.containerRect;
        const x = (screenX / rect.width) * 2 - 1;
        const y = -(screenY / rect.height) * 2 + 1;

        const vector = new THREE.Vector3(x, y, 0.5);
        vector.unproject(this.camera);

        const dir = vector.sub(this.camera.position).normalize();
        const dist = -this.camera.position.z / dir.z;

        this.position.copy(this.camera.position).add(dir.multiplyScalar(dist));
        this.mesh.position.copy(this.position);

        // Pulsing effect only during attraction/absorption
        if (this.pulsing) {
            const t = Date.now() * 0.001;
            const pulse = 1 + Math.sin(t * 5) * 0.1;
            this.mesh.scale.set(3 * pulse, 3 * pulse, 1);
        }
    }


    deactivate() {
        this.isActive = false;
        this.pulsing = false;

        if (window.TWEEN) {
            new TWEEN.Tween(this.mesh.material)
                .to({ opacity: 0 }, 300)
                .onComplete(() => {
                    this.mesh.scale.set(0, 0, 1);
                })
                .start();
        }

        return this.absorbedCount;
    }


    expandToHexagram() {
        // Stop heartbeat pulsing
        this.pulsing = false;

        // Smooth “breathing expansion” so it looks more zen
        if (window.TWEEN) {
            new TWEEN.Tween(this.mesh.scale)
                .to({ x: 12, y: 12 }, 1600)  // slower, softer
                .easing(TWEEN.Easing.Cubic.Out)
                .start();

            // Ink-like fade-out
            new TWEEN.Tween(this.mesh.material)
                .to({ opacity: 0.0 }, 1600)
                .easing(TWEEN.Easing.Quadratic.InOut)
                .start();
        }
    }


    dispose() {
        if (this.mesh) {
            this.scene.remove(this.mesh);
        }
    }
}