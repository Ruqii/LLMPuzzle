// app.js - Main application orchestration

const THREE = window.THREE;
const TWEEN = window.TWEEN;

const { ParticleSystem } = window; // 管letters rain, 文字被吸进黑洞， emit particles生成卦象
const { BlackHole } = window; // 黑洞位置，吸引逻辑， 黑洞呼吸， 计数absorbed letters
const { Hexagram } = window; // 接收粒子， 排队， 按顺序画出卦象

class App {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.particleSystem = null;
        this.blackHole = null;
        this.hexagram = null;

        this.state = 'RAIN'; 

        this._hexagramCompletedCount = 0; //oh no 不要忘了初始化 girl，不然不会移动
        this.pointer = { x: 0, y: 0, isDown: false };
        this.hexagramTimeout = null;

        this.init();
        this.setupEventListeners();
        this.animate();
    }

    init() {
        this.scene = new THREE.Scene();

        this.camera = new THREE.PerspectiveCamera(
            75,
            window.innerWidth / window.innerHeight,
            0.1,
            1000
        );
        this.camera.position.z = 15;

        this.camera.userData.containerRect = {
            width: window.innerWidth,
            height: window.innerHeight
        };

        this.renderer = new THREE.WebGLRenderer({
            antialias: true,
            alpha: true
        });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.setClearColor(0x000000, 1);

        document
            .getElementById('canvas-container')
            .appendChild(this.renderer.domElement);

        this.particleSystem = new ParticleSystem(this.scene, this.camera, this.renderer);
        this.blackHole = new BlackHole(this.scene, this.camera);

        setTimeout(() => {
            const loading = document.getElementById('loading');
            if (loading) loading.classList.add('hidden');
        }, 500);
    }

    // 输入控制
    setupEventListeners() {
        const canvas = this.renderer.domElement;

        canvas.addEventListener('pointerdown', (e) => this.onPointerDown(e));
        canvas.addEventListener('pointermove', (e) => this.onPointerMove(e));
        canvas.addEventListener('pointerup', (e) => this.onPointerUp(e));
        canvas.addEventListener('pointercancel', (e) => this.onPointerUp(e));

        canvas.addEventListener('contextmenu', (e) => e.preventDefault());

        window.addEventListener('resize', () => this.onResize());
    }

    // 启动黑洞
    onPointerDown(event) {
        if (this.state === 'HEXAGRAM') {
            this.resetToRain();
            return;
        }

        this.pointer.isDown = true;
        this.pointer.x = event.clientX;
        this.pointer.y = event.clientY;

        this.state = 'ATTRACTING';
        // this.blackHole.activate(this.pointer.x, this.pointer.y);
        // Always activate at screen center
        const rect = this.renderer.domElement.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        this.blackHole.activate(centerX, centerY);

        if (this.hexagramTimeout) {
            clearTimeout(this.hexagramTimeout);
            this.hexagramTimeout = null;
        }
    }


    // 移动黑洞 
    onPointerMove(event) {
        if (!this.pointer.isDown) return;

        this.pointer.x = event.clientX;
        this.pointer.y = event.clientY;

        // Black hole stays fixed, so no need to move it
        // if (this.state === 'ATTRACTING') {
        //     this.blackHole.update(this.pointer.x, this.pointer.y);
        // }
    }

    // 吸收检测
    onPointerUp(event) {
        if (!this.pointer.isDown) return;

        this.pointer.isDown = false;

        if (this.state === 'ATTRACTING') {
            this.state = 'ABSORBING';
            this.particleSystem._absorbStartTime = performance.now();
        }
    }

    //  这里我用了一个例子来测试，接入backend之后可以改掉
    // test hexagram before backend
    getExampleHexagram() {
        // 1 = Yang (solid line)
        // 0 = Yin  (dash line)
        //
        return {
            left:  [1, 0, 1, 1, 0, 0],   
            right: [0, 1, 0, 0, 1, 1]    
        };
    }

     // 改成两个卦象function
    showDoubleHexagram() {
        if (this.state === 'HEXAGRAM') return;

        this.state = 'HEXAGRAM';
        console.log("showDoubleHexagram");

        this.blackHole.expandToHexagram();

        // 清除旧卦象
        if (this.hexLeft) this.hexLeft.dispose();
        if (this.hexRight) this.hexRight.dispose();

        const offset = 2.8; // 两个卦象的宽度
        const center = this.blackHole.position.clone();

        const posLeft = center.clone().add(new THREE.Vector3(-offset, 0, 0));
        const posRight = center.clone().add(new THREE.Vector3(offset, 0, 0));

        // 拿到例子卦象
        const { left, right } = this.getExampleHexagram();

        // 直接把阴阳数组传给 Hexagram 构造函数
        //  和之前单卦版本保持一致）
        this.hexLeft  = new Hexagram(this.scene, posLeft,  left);
        this.hexRight = new Hexagram(this.scene, posRight, right);

        // 监听完成事件
        this._hexagramCompletedCount = 0;
        this.hexLeft.onComplete  = () => this.tryMoveHexagramsUp();
        this.hexRight.onComplete = () => this.tryMoveHexagramsUp();

        // 计算总需要粒子数
        // const totalNeeded =
        //     this.hexLeft.actualParticlesNeeded +
        //     this.hexRight.actualParticlesNeeded;
        const totalNeeded =
            (this.hexLeft.actualParticlesNeeded  || 260) +
            (this.hexRight.actualParticlesNeeded || 260);

        console.log(`emitting ${totalNeeded} particles`);

        // 粒子交替assign给左右卦象
        let toggle = false;

        this.particleSystem.emitFormationParticles(
            this.blackHole.position,
            totalNeeded,
            p => {
                if (toggle) this.hexLeft.enqueueParticle(p);
                else this.hexRight.enqueueParticle(p);
                toggle = !toggle;
            }
        );

        // 延迟开始形成
        setTimeout(() => {
            this.hexLeft.startFormation();
            this.hexRight.startFormation();
        }, 900);

        this.hexagramTimeout = setTimeout(() => {
            this.resetToRain();
        }, 15000);
    }


    tryMoveHexagramsUp() {
        this._hexagramCompletedCount++;
        if (this._hexagramCompletedCount < 2) return;

        const targetY = 6.5; // 位移的高度在这里改
        const duration = 1800;

        new TWEEN.Tween(this.hexLeft.position)
            .to({ y: targetY }, duration)
            .easing(TWEEN.Easing.Cubic.Out)
            .start();

        new TWEEN.Tween(this.hexRight.position)
            .to({ y: targetY }, duration)
            .easing(TWEEN.Easing.Cubic.Out)
            .start();

        console.log("Both hexagrams formed → moving upward");
    }


    resetToRain() {
        this.state = 'RAIN';

        if (this.hexLeft) this.hexLeft.hide();
        if (this.hexRight) this.hexRight.hide();

        if (this.hexagramTimeout) {
            clearTimeout(this.hexagramTimeout);
            this.hexagramTimeout = null;
        }

        this.blackHole.deactivate();
    }

    onResize() {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        if (window.TWEEN) TWEEN.update();

        if (this.state !== 'HEXAGRAM') {
            const isAbsorbing = this.state === 'ABSORBING';
            const bh = (this.state === 'ATTRACTING' || this.state === 'ABSORBING')
                ? this.blackHole
                : null;

            this.particleSystem.update(bh, isAbsorbing);

            if (this.state === 'ABSORBING') {
                const total = this.particleSystem.getParticleCount();
                const near = this.countLettersNearBlackHole();

                if (total < 20 && near === 0 && this.blackHole.absorbedCount > 5) {
                    this.showDoubleHexagram();
                }
            }
        }

        // 两个卦象同时 update
        if (this.state === 'HEXAGRAM') {
            if (this.hexLeft) this.hexLeft.update();
            if (this.hexRight) this.hexRight.update();
        }

        this.renderer.render(this.scene, this.camera);
    }

    countLettersNearBlackHole() {
        const radius = this.blackHole.radius * 4;
        let count = 0;

        this.particleSystem.columns.forEach(col => {
            col.letters.forEach(l => {
                const dx = l.position.x - this.blackHole.position.x;
                const dy = l.position.y - this.blackHole.position.y;
                if (Math.sqrt(dx*dx + dy*dy) < radius) count++;
            });
        });

        return count;
    }

}

window.app = new App();
