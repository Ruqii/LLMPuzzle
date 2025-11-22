import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# ---- 后端设置：让动画在所有环境都能显示 ----
# 对于 VSCode / PyCharm / Mac 最稳的是 TkAgg
try:
    matplotlib.use("TkAgg")
except:
    pass

# ---- 图形设置 ----
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xlim(-7, 7)
ax.set_ylim(-7, 7)
ax.set_aspect('equal')
ax.axis('off')

fig.patch.set_facecolor('white')
ax.set_facecolor('white')

# ---- 六爻（1=阳爻=整圆，0=阴爻=断爻）----
# 你可以改成任何卦，例如：
# hexagram = [1,1,0,1,0,0]
hexagram = [1, 0, 1, 1, 0, 1]

# ---- 半径设置 ----
num_circles = 6
radii = np.linspace(1, 6, num_circles)

# ---- 阴爻 / 阳爻的 θ（角度分布） ----
def get_theta(is_yin):
    if is_yin:
        # 阴爻：缺口 50°
        full = np.linspace(0, 2*np.pi - np.radians(50), 400)
        return full
    else:
        # 阳爻：360°
        return np.linspace(0, 2*np.pi, 400)

# 六个圆的角度数组
thetas = [get_theta(v == 0) for v in hexagram]

# ---- 初始化线条对象 ----
lines = []
for i in range(num_circles):
    line, = ax.plot([], [], linewidth=3)
    lines.append(line)

# ---- 动画初始化 ----
def init():
    for line in lines:
        line.set_data([], [])
    return tuple(lines)

# ---- 动画帧更新 ----
def update(frame):
    for i, (line, radius, theta) in enumerate(zip(lines, radii, thetas)):

        # 每一圈不同旋转速度
        rotation_deg = frame * (i + 1) * 0.2
        rotation_rad = np.radians(rotation_deg)

        # 旋转后的坐标
        x = radius * np.cos(theta + rotation_rad)
        y = radius * np.sin(theta + rotation_rad)

        # 色彩流动（能量沿圆周移动）
        color_phase = (frame * 0.01 + i * 0.15) % 1.0
        line.set_color(plt.cm.plasma(color_phase))

        line.set_data(x, y)

    return tuple(lines)

# ---- 创建动画 ----
anim = FuncAnimation(
    fig,
    update,
    init_func=init,
    frames=1000,
    interval=40,
    repeat=True,
    blit=False  # 关闭 blit，兼容所有后端
)

plt.show()