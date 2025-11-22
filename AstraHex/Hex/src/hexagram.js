// Hexagram.js
// Usage: new Hexagram(scene, center, [1,0,1,1,0,0])

window.Hexagram = class Hexagram {
    constructor(scene, position, yinYangArray) {
        this.scene = scene;
        this.position = position.clone();
        this.yinYangArray = yinYangArray;   // [1,0,1,1,0,0]

        this.lines = [];
        this.isAnimating = false;
        this.formationComplete = false;

        this.lineCount = 6;
        this.lineSpacing = 0.6;
        this.lineWidth = 2.6;

        // density: 每单位宽度多少粒子
        this.density = 60;

        this.particleQueue = [];
        this.activationTimeouts = [];

        // 给 app 用的：总共需要多少粒子
        this.actualParticlesNeeded = 0;

        // 方便 dispose 的时候移除
        this.usedParticles = [];
        // 记录上一次的位置
        this._prevY = this.position.y;

        this.createLines();

        // 要加一个callback
        this.onComplete = null;
    }

    // 提供给外部使用：告诉 particleSystem 要生成多少粒子
    getTotalParticlesNeeded() {
        return this.lines.reduce((sum, l) => sum + l.neededParticles, 0);
    }

    createLines() {
        const startY = this.position.y - (this.lineCount - 1) * this.lineSpacing / 2;

        for (let i = 0; i < this.lineCount; i++) {
            const yinYang = this.yinYangArray[i]; // 1 = yang, 0 = yin
            const y = startY + i * this.lineSpacing;

            const line = this.createSingleLine(y, this.lineWidth, yinYang);
            // 记住相对位移（为了之后整体移动 hexagram）
            line.yOffset = line.mesh.position.y - this.position.y;
            line.xOffset = line.mesh.position.x - this.position.x;
            this.lines.push(line);
        }

        const needed = this.getTotalParticlesNeeded();
        this.actualParticlesNeeded = needed;
        console.log(`Hexagram requires total ${needed} particles`);
    }

    createSingleLine(y, width, yinYangType) {
        const geom = new THREE.PlaneGeometry(width, 0.16);
        const mat = new THREE.MeshBasicMaterial({
            color: 0xffffff,
            transparent: true,
            opacity: 0
        });

        const mesh = new THREE.Mesh(geom, mat);
        mesh.position.set(this.position.x, y, this.position.z);
        mesh.visible = false; 
        this.scene.add(mesh);

        // 阳爻（实线）
        if (yinYangType === 1) {
            const needed = Math.floor(width * this.density);

            return {
                y,
                width,
                type: "yang",
                mesh,
                segments: [{ start: 0, end: 1 }],
                neededParticles: needed,
                particles: [],
                isActive: false,
                isFormed: false,

                xOffset: 0,
                yOffset: 0
            };
        }

        // 阴爻（断线）
        const gap = 0.22; // 中间缺口比例
        const leftEnd = (1 - gap) / 2;
        const rightStart = 1 - leftEnd;

        const neededLeft = Math.floor(leftEnd * this.density * width);
        const neededRight = Math.floor(leftEnd * this.density * width);
        const needed = neededLeft + neededRight;

        return {
            y,
            width,
            type: "yin",
            mesh,
            segments: [
                { start: 0, end: leftEnd },
                { start: rightStart, end: 1 }
            ],
            neededParticles: needed,
            particles: [],
            isActive: false,
            isFormed: false,

            xOffset: 0,
            yOffset: 0
        };
    }

    // 外部会把新生成的粒子丢给我们
    enqueueParticle(p) {
        this.particleQueue.push(p);
        this.usedParticles.push(p);
    }

    // 开始生成卦象
    startFormation() {
        if (this.isAnimating) return;

        console.log("Hexagram formation begins");

        this.isAnimating = true;
        this.formationComplete = false;

        // 激活第一条线
        this.activateLine(0);
    }

    activateLine(i) {
        if (i >= this.lineCount) {
            console.log("All 6 lines complete");
            this.formationComplete = true;

            if (typeof this.onComplete === "function") {
                this.onComplete();
            }
            return;
        }

        const line = this.lines[i];
        line.isActive = true;
        line.isFormed = false;

        console.log(`Line ${i + 1} ACTIVATED`);
    }

    // 每帧调用
    update() {

        // 先计算这一帧 hexagram 在 y 轴上移动了多少
        const dy = this.position.y - this._prevY;
        if (dy !== 0) {
            // 把所有已经在卦象里的粒子整体往上/下平移
            this.lines.forEach(line => {
                line.particles.forEach(p => {
                    p.position.y += dy;
                    if (p.userData.targetPos) {
                        p.userData.targetPos.y += dy;
                    }
                });
            });
            // 更新 prevY，准备下一帧
            this._prevY = this.position.y;
        }

        // 每帧同步 line.mesh 位置（确保 tween 生效）
        this.lines.forEach(line => {
            line.mesh.position.x = this.position.x + line.xOffset;
            line.mesh.position.y = this.position.y + line.yOffset;
        });

        this.lines.forEach(line => {
            line.mesh.position.y = this.position.y + line.yOffset;
        });

        // 1. 把粒子塞进正在成型的线
        this.lines.forEach((line, index) => {
            if (!line.isActive || line.isFormed) return;

            const remaining = line.neededParticles - line.particles.length;
            if (remaining <= 0) return;
            if (this.particleQueue.length === 0) return;

            const take = Math.min(remaining, this.particleQueue.length, 3);

            for (let n = 0; n < take; n++) {
                const p = this.particleQueue.shift();
                if (!p) continue;

                const t = line.particles.length / line.neededParticles;

                // 选择 segment（阴爻用左右两段，阳爻就是整段）
                const segment = line.segments.length === 1
                    ? line.segments[0]
                    : line.segments[Math.random() < 0.5 ? 0 : 1];

                const segT = segment.start + t * (segment.end - segment.start);

                const x = line.mesh.position.x - line.width / 2 + segT * line.width;
                const y = line.mesh.position.y + (Math.random() - 0.5) * 0.03;

                p.userData.targetPos = new THREE.Vector3(x, y, this.position.z);
                p.userData.lockProgress = 0;
                p.userData.isForming = true;  // 供 particleSystem 判断

                // 为每个粒子存一份自己的速度 & 漂浮相位
                if (p.userData.speed == null) {
                    p.userData.speed = 0.008 + Math.random() * 0.012; // 比较慢
                }
                if (p.userData.noisePhaseX == null) {
                    p.userData.noisePhaseX = Math.random() * Math.PI * 2;
                    p.userData.noisePhaseY = Math.random() * Math.PI * 2;
                    p.userData.noiseAmp = 0.004 + Math.random() * 0.003;
                }

                line.particles.push(p);
            }

        });

        // 2. 移动粒子到目标位置 & 检查线是否完成
        this.lines.forEach((line, index) => {
            if (!line.isActive || line.isFormed) return;

            let locked = 0;

            line.particles.forEach(p => {
                if (!p.userData.targetPos) return;

                const target = p.userData.targetPos;

                // 每个粒子有自己的速度，避免每帧随机造成“抖动”
                const baseSpeed = p.userData.speed || 0.01;
                p.userData.lockProgress = Math.min(1, p.userData.lockProgress + baseSpeed);

                const t = p.userData.lockProgress;

                // 仍然用一个 S-curve，但我们把随机感放到 noise 里
                const ease = Math.pow(t, 1.5) * (2 - t);

                // 漂浮噪声：每个粒子有自己的相位和振幅，随时间缓慢变化
                p.userData.noisePhaseX += 0.03;
                p.userData.noisePhaseY += 0.027;
                const amp = p.userData.noiseAmp || 0.005;

                const noiseX = Math.sin(p.userData.noisePhaseX) * amp;
                const noiseY = Math.cos(p.userData.noisePhaseY) * amp;

                // 更慢、更柔地靠拢，同时带一点漂浮感
                p.position.x += (target.x - p.position.x) * (0.05 + ease * 0.12) + noiseX;
                p.position.y += (target.y - p.position.y) * (0.05 + ease * 0.10) + noiseY;

                // 轻柔淡入
                p.material.opacity = Math.min(1, p.material.opacity + 0.03);

                if (t > 0.95) locked++;
            });

            // 根据锁定比例让线本身亮起来一点
            const stability = locked / line.neededParticles;
            line.mesh.material.opacity = Math.pow(stability, 0.7) * 0.9;

            if (locked >= line.neededParticles * 0.9) {
                line.isFormed = true;
                console.log(`✓ Line ${index + 1} formed`);

                // 激活下一条线
                this.activateLine(index + 1);
            }
        });

        // 检测整个卦象是否完成
        if (!this.formationComplete) {
            const allFormed = this.lines.every(l => l.isFormed);
            if (allFormed) {
                this.formationComplete = true;
                console.log("Hexagram fully formed!");

                if (typeof this.onComplete === "function") {
                    this.onComplete();
                }
            }
        }
    }

    // 只隐藏线条（恢复雨的时候用）
    hide() {
        this.lines.forEach(line => {
            if (line.mesh && line.mesh.material) {
                line.mesh.material.opacity = 0;
            }
        });
    }

    // 彻底清理掉（重新生成卦象时用）
    dispose() {
        console.log("Disposing hexagram…");
        // 清 timeout（如果之后你要加）
        this.activationTimeouts.forEach(id => clearTimeout(id));
        this.activationTimeouts = [];

        // 移除线 mesh
        this.lines.forEach(line => {
            if (line.mesh) {
                this.scene.remove(line.mesh);
                if (line.mesh.geometry) line.mesh.geometry.dispose();
                if (line.mesh.material) line.mesh.material.dispose();
            }
        });

        // 移除已经被我们用过的粒子（不强制必须，主要是避免 scene 太脏）
        this.usedParticles.forEach(p => {
            if (p && p.parent === this.scene) {
                this.scene.remove(p);
            }
        });

        this.lines = [];
        this.particleQueue = [];
        this.usedParticles = [];
        this.isAnimating = false;
        this.formationComplete = true;
    }
};
