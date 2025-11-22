// particleSystem.js - Manages falling text particles (clean version)

window.ParticleSystem = class ParticleSystem {
    constructor(scene, camera, renderer) {
        this.scene = scene;
        this.camera = camera;
        this.renderer = renderer;

        this.columns = [];
        this.maxColumns = this.isMobile() ? 40 : 80;

        // 专门给卦象用的 formation 粒子
        this.formationParticles = [];

        // 吸力阶段控制
        this._absorbStartTime = 0;
        this._forceAbsorb = false;

        this.poem = [
            "when you touch the silence,",
            "time breathes.",
            "every moment writes itself,",
            "then disappears, into your hand.",
            "what remains, is not the word,",
            "but the pattern it leaves.",
            "your fingerprint of time.",
            "when",
            "time",
            "every",
            "moment",
            "times,",
            "your",
            "fingerprint"
        ];

        // 修复：字体 load 阻塞导致 init() 不执行
        this.waitFontsThenInit();
    }

    isMobile() {
        return window.innerWidth < 800 || /Android|webOS|iPhone|iPad|iPod/i.test(navigator.userAgent);
    }

    // 修复版 waitFontsThenInit: 字体 load 最多等待 300ms，不阻塞 init()
    async waitFontsThenInit() {
        try {
            await Promise.race([
                document.fonts.load('600 28px "Inter"'),
                new Promise(resolve => setTimeout(resolve, 300)) // 防止永久等待
            ]);
            console.log('✓ Inter font loaded or skipped');
        } catch (e) {
            console.warn("⚠ Font load failed, continuing anyway");
        }

        this.init(); // 无论字体是否成功，都执行
    }

    // 初始化letters rain
    init() {
        for (let i = 0; i < this.maxColumns; i++) this.createColumn();

        const totalLetters = this.columns.reduce(
            (sum, col) => sum + col.letters.length,
            0
        );
        console.log(`✓ ParticleSystem ready: ${totalLetters} falling letters`);
    }


    //  文字雨列, not very obvious though, maybe need to enhance later
    createColumn(x = null, y = null) {
        const line = this.poem[Math.floor(Math.random() * this.poem.length)];
        let chars = [...line].filter(ch => ch !== " ");

        if (chars.length > 40) chars = chars.slice(0, 40);

        const frustumHeight =
            2 * Math.tan((this.camera.fov * Math.PI) / 360) *
            Math.abs(this.camera.position.z);
        const frustumWidth = frustumHeight * this.camera.aspect;

        const columnX = x ?? ((Math.random() - 0.5) * frustumWidth * 1.3);
        const startY = y ?? ((Math.random() - 0.5) * frustumHeight * 1.8);

        const spacing = 0.8;
        const letters = [];

        chars.forEach((ch, i) => {
            const sprite = this.createLetterSprite(ch, i, chars.length);

            sprite.position.x = columnX + (Math.random() - 0.5) * 0.1;
            sprite.position.y = startY - i * spacing;
            sprite.position.z = Math.random() * -5;

            sprite.userData = {
                velocity: new THREE.Vector3(
                    (Math.random() - 0.5) * 0.003,
                    -0.01 - Math.random() * 0.015,
                    0
                ),
                originalVelocity: new THREE.Vector3()
            };
            sprite.userData.originalVelocity.copy(sprite.userData.velocity);

            this.scene.add(sprite);
            letters.push(sprite);
        });

        this.columns.push({ letters, columnX });
    }

    createLetterSprite(letter, index, total) {
        const canvas = document.createElement("canvas");
        const size = 80;

        canvas.width = size;
        canvas.height = size;

        const ctx = canvas.getContext("2d");
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.font = `600 48px "Inter", sans-serif`;

        const alpha = 0.5 + (index / total) * 0.5;
        ctx.fillStyle = `rgba(255,255,255,${alpha})`;

        ctx.shadowColor = "rgba(255,255,255,0.6)";
        ctx.shadowBlur = 8;

        ctx.fillText(letter, size / 2, size / 2);

        const texture = new THREE.CanvasTexture(canvas);
        const sprite = new THREE.Sprite(
            new THREE.SpriteMaterial({
                map: texture,
                transparent: true,
                opacity: 1.0
            })
        );

        sprite.scale.set(1.2, 1.2, 1);
        return sprite;
    }

 
    //  卦象 Formation 粒子
    createFormationParticle(position) {
        const canvas = document.createElement("canvas");
        const size = 18;
        canvas.width = size;
        canvas.height = size;

        const ctx = canvas.getContext("2d");
        const g = ctx.createRadialGradient(size/2, size/2, 0, size/2, size/2, size/2);
        g.addColorStop(0, "rgba(255,255,255,0.85)");
        g.addColorStop(1, "rgba(255,255,255,0)");

        ctx.fillStyle = g;
        ctx.fillRect(0, 0, size, size);

        const sprite = new THREE.Sprite(
            new THREE.SpriteMaterial({
                map: new THREE.CanvasTexture(canvas),
                transparent: true,
                opacity: 0,
                blending: THREE.AdditiveBlending
            })
        );

        sprite.scale.set(0.15, 0.15, 1);
        sprite.position.copy(position);

        sprite.userData = {
            fadeIn: 0,
            velocity: new THREE.Vector3(),
            lockProgress: 0,
            targetPos: null,
            // isForming 会在 hexagram.enqueueParticle() 设置
        };

        return sprite;
    }

    emitFormationParticles(center, count = 240, onNewParticle = null) {
        let generated = 0;
        const batchSize = 5;

        this.formationStartTime = performance.now();
        this.formationParticles = [];

        const emitBatch = () => {
            for (let i = 0; i < batchSize && generated < count; i++) {
                const p = this.createFormationParticle(center.clone());

                const angle = Math.random() * Math.PI * 2;
                const radius = Math.random() * 0.18;
                p.position.x += Math.cos(angle) * radius;
                p.position.y += Math.sin(angle) * radius;

                const speed = 0.015 + Math.random() * 0.085;
                p.userData.velocity.set(
                    Math.cos(angle) * speed,
                    Math.sin(angle) * speed,
                    0
                );

                this.scene.add(p);
                this.formationParticles.push(p);

                if (onNewParticle) onNewParticle(p);

                generated++;
            }

            if (generated < count) requestAnimationFrame(emitBatch);
        };

        emitBatch();
    }


    // UPDATE LOOP
    update(blackHole = null, isAbsorbing = false) {
        // 1. 黑洞吸力阶段
        if (isAbsorbing && this._absorbStartTime) {
            const dt = performance.now() - this._absorbStartTime;
            this._forceAbsorb = dt > 1800;
        } else {
            this._forceAbsorb = false;
        }

        // 2. camera高度
        const frustumHeight =
            2 * Math.tan((this.camera.fov * Math.PI) / 360) *
            Math.abs(this.camera.position.z);

        // 3. Falling Letters 更新
        for (let colIdx = 0; colIdx < this.columns.length; colIdx++) {
            const column = this.columns[colIdx];
            const letters = column.letters;

            for (let i = letters.length - 1; i >= 0; i--) {
                const l = letters[i];

                // 黑洞吸力逻辑保持不变
                if (blackHole && blackHole.isActive) {
                    const dx = blackHole.position.x - l.position.x;
                    const dy = blackHole.position.y - l.position.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    let absorbFactor = 0;
                    if (isAbsorbing && this._absorbStartTime) {
                        absorbFactor = Math.min(
                            1,
                            (performance.now() - this._absorbStartTime) / 2500
                        );
                    }

                    const baseForce = 0.00035;
                    const easeDist = Math.max(0.12, dist);
                    const distFalloff = 1 / (easeDist * 0.9 + 1.2);
                    const absorbGain = absorbFactor * absorbFactor;

                    const force =
                        baseForce * (0.12 + absorbGain * 2.3) * distFalloff;

                    l.userData.velocity.x += dx * force;
                    l.userData.velocity.y += dy * force;

                    // Stage 2 吞入
                    if (dist < blackHole.radius * 0.38) {
                        this.scene.remove(l);
                        letters.splice(i, 1);
                        blackHole.absorbedCount++;
                        continue;
                    }

                    // Stage 3 强制吞入, 这里有点不自然，最后再调吧，心累
                    if (this._forceAbsorb) {
                        l.userData.velocity.x += dx * 0.0008;
                        l.userData.velocity.y += dy * 0.0008;
                        l.userData.velocity.multiplyScalar(0.982);

                        if (dist < blackHole.radius * 0.4) {
                            this.scene.remove(l);
                            letters.splice(i, 1);
                            blackHole.absorbedCount++;
                            continue;
                        }
                    }
                }

                // 正常掉落
                l.position.add(l.userData.velocity);

                // 非吸力阶段：掉出屏幕则回顶部
                if (l.position.y < -frustumHeight / 2 - 2 && !isAbsorbing) {
                    l.position.y = frustumHeight / 2 + Math.random() * 5;
                    continue;
                }

                // 吸力阶段：掉出屏幕则删除
                if (l.position.y < -frustumHeight / 2 - 2 && isAbsorbing) {
                    this.scene.remove(l);
                    letters.splice(i, 1);
                }
            }

            if (letters.length === 0) {
                this.columns.splice(colIdx, 1);
                colIdx--;
            }
        }

        // 4. Formation 粒子更新（兼容双卦象）
        let hexagramActive = false;
        let hexagramComplete = false;

        if (window.app) {
            const L = window.app.hexLeft;
            const R = window.app.hexRight;

            if (L && L.isAnimating) hexagramActive = true;
            if (R && R.isAnimating) hexagramActive = true;

            // 两个卦象任意一个未完成 → 不 complete
            if (L && L.formationComplete && R && R.formationComplete) {
                hexagramComplete = true;
            }
        }

        // 两个卦象都完成 → 不再更新 formation 粒子（让它们保持静止）
        if (hexagramComplete) return;

        // formation 开始约 100ms 后再进入视觉效果
        if (this.formationStartTime &&
            performance.now() - this.formationStartTime > 100) 
        {
            this.formationParticles.forEach(p => {

                // 1) 粒子淡入
                if (p.userData.fadeIn < 1) {
                    p.userData.fadeIn += 0.035;
                    p.material.opacity = p.userData.fadeIn * 0.85;
                }

                // 2) 卦象正在形成 → 停止所有漂散速度
                if (hexagramActive) {
                    if (p.userData.velocity) {
                        p.userData.velocity.set(0,0,0);
                    }
                    return; // ❗不要漂散
                }

                // 3) 卦象未开始 → 粒子继续往外漂
                if (p.userData.velocity) {
                    p.position.add(p.userData.velocity);
                    p.userData.velocity.multiplyScalar(0.965);
                }
            });
        }
    }

    clear() {
        this.columns.forEach((col) =>
            col.letters.forEach((l) => this.scene.remove(l))
        );
        this.columns = [];
    }

    getParticleCount() {
        let count = 0;
        this.columns.forEach((col) => {
            count += col.letters.length;
        });
        return count;
    }
};
