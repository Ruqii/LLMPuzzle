import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


STAR_SCORES = {
    # 主星
    "紫微": 10, "天机": 7, "太阳": 8, "武曲": 9, "天同": 3, "廉贞": 8,
    "天府": 8, "太阴": 7, "贪狼": 10, "巨门": 7, "天相": 7, "天梁": 6,
    "七杀": 10, "破军": 9,
    # 六吉星
    "左辅": 3, "右弼": 3, "文昌": 3, "文曲": 2, "天魁": 4, "天钺": 4,
    # 六煞星
    "擎羊": -3, "陀罗": -3, "火星": -4, "铃星": -4, "地空": -2, "地劫": -2,
    # 杂曜
    "红鸾": 2, "天喜": 2, "天姚": 1, "天哭": -1, "天虚": -1,
    "天德": 2, "月德": 2, "龙池": 1, "凤阁": 1, "天巫": 1,
    "恩光": 2, "天贵": 2,
    # 四化星
    "化禄": 3, "化权": 2, "化科": 1, "化忌": -3
}


# Weights for each palace in the six dimensions
PALACE_WEIGHTS = {
    "Selfness": {"命宫": 0.6, "福德宫": 0.4},
    "Relationships": {"夫妻宫": 0.6, "兄弟宫": 0.4},
    "Family & Legacy": {"父母宫": 0.5, "田宅宫": 0.5},
    "Wealth & Resources": {"财帛宫": 0.6, "子女宫": 0.4},
    "Resilience & Transformation": {"疾厄宫": 0.5, "迁移宫": 0.5},
    "Career & Mission": {"官禄宫": 0.6, "交友宫": 0.4}
}


# calculate palace score including empty palace 
def calculate_palace_score(stars):
    if not stars:  # 空宫
        return 1
    return sum(STAR_SCORES.get(s, 0) for s in stars)


# calculate all palace scores
def calculate_all_palace_scores(chart_dict):
    return {palace: calculate_palace_score(stars) for palace, stars in chart_dict.items()}


# 加入身宫修正
def apply_body_palace_effect(palace_scores, body_palace, body_main_star):
    corrected = {}
    body_score = palace_scores.get(body_palace, 0)
    main_star_score = STAR_SCORES.get(body_main_star, 0)
    for palace, score in palace_scores.items():
        if palace == body_palace:
            corrected[palace] = score + body_score + main_star_score * 0.5
        else:
            corrected[palace] = score
    return corrected


# cLalculate six dimension scores
def calculate_dimension_scores(palace_scores, gamma=1.3):
    dims = {}
    for dim, mapping in PALACE_WEIGHTS.items():
        score = sum(palace_scores.get(p, 0) * w for p, w in mapping.items())
        dims[dim] = score

    # ---- 平滑指数映射 (Gamma Mapping) ----
    min_score = min(dims.values()) if dims else 0
    max_score = max(dims.values()) if dims else 1

    mapped = {}
    for k, v in dims.items():
        norm = (v - min_score) / (max_score - min_score + 1e-9)  # 防止除0
        mapped[k] = round(40 + 60 * (norm ** gamma), 1)

    return mapped


# example
chart_example = {
    "命宫": ["紫微", "文昌", "红鸾"],
    "福德宫": ["天同", "天德"],
    "夫妻宫": ["太阴", "天喜"],
    "兄弟宫": ["天机"],
    "父母宫": ["天梁"],
    "田宅宫": ["天府", "天德"],
    "财帛宫": ["武曲", "左辅", "化禄"],
    "子女宫": ["贪狼", "文曲"],
    "疾厄宫": ["破军", "火星"],
    "迁移宫": ["七杀"],  # 身宫
    "官禄宫": ["太阳", "天魁"],
    "交友宫": ["廉贞", "右弼"]
}

BODY_PALACE = "迁移宫"
BODY_MAIN_STAR = "七杀"


# main
if __name__ == "__main__":
    # 计算宫位scores
    palace_scores = calculate_all_palace_scores(chart_example)

    # 加入身宫
    palace_scores_corrected = apply_body_palace_effect(palace_scores, BODY_PALACE, BODY_MAIN_STAR)

    # 就散六维scores
    dim_scores = calculate_dimension_scores(palace_scores_corrected)

    print("palace scores (with Body Palace):")
    for k, v in palace_scores_corrected.items():
        print(f"{k}: {v}")

    print("\n six dimension scores (0-100):")
    for k, v in dim_scores.items():
        print(f"{k}: {v}")

   
    # Radar chart
    labels = list(dim_scores.keys())
    values = list(dim_scores.values())
    values += values[:1]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    ax.plot(angles, values, marker='o', linewidth=2, color='#c19a6b')
    ax.fill(angles, values, alpha=0.3, color='#deb887')
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_title("6D Personality Radar", size=13, pad=20)
    ax.spines['polar'].set_color('#8b7355')
    plt.show()




from scipy.stats import norm

# === 映射函数 ===
def gamma_mapping(x, gamma=1.3):
    norm = (x - (-20)) / (40)  # normalize to [0,1]
    return 40 + 60 * (norm ** gamma)

def cdf_mapping(x, mu=0, sigma=10):
    return 40 + 60 * norm.cdf((x - mu) / sigma)


# === 对比绘图 ===
x = np.linspace(-20, 20, 400)
y_gamma = gamma_mapping(x, gamma=1.3)
y_cdf = cdf_mapping(x, mu=0, sigma=10)
y_linear = 40 + 1.5 * (x + 20)

plt.figure(figsize=(8,5))
plt.plot(x, y_linear, '--', color='gray', label='Linear')
plt.plot(x, y_gamma, color='#c19a6b', label='Gamma=1.3 Mapping')
plt.plot(x, y_cdf, color='#4682b4', label='Normal CDF (μ=0, σ=10)')
plt.xlabel("Input [-20, 20]")
plt.ylabel("Mapped Score [40, 100]")
plt.title("Mapping Comparison: Linear vs Gamma vs CDF")
plt.legend()
plt.grid(alpha=0.3)
plt.show()




from scipy.stats import norm

# === 计算六维分数（Gamma & CDF 两种映射） ===
def calculate_dimension_scores_gamma(palace_scores, gamma=1.3):
    dims = {}
    for dim, mapping in PALACE_WEIGHTS.items():
        score = sum(palace_scores.get(p, 0) * w for p, w in mapping.items())
        dims[dim] = score

    min_score = min(dims.values()) if dims else 0
    max_score = max(dims.values()) if dims else 1
    mapped = {}
    for k, v in dims.items():
        normed = (v - min_score) / (max_score - min_score + 1e-9)
        mapped[k] = round(40 + 60 * (normed ** gamma), 1)
    return mapped


def calculate_dimension_scores_cdf(palace_scores, mu=0, sigma=10):
    dims = {}
    for dim, mapping in PALACE_WEIGHTS.items():
        score = sum(palace_scores.get(p, 0) * w for p, w in mapping.items())
        dims[dim] = score

    min_score = min(dims.values()) if dims else 0
    max_score = max(dims.values()) if dims else 1
    mapped = {}
    for k, v in dims.items():
        normed = (v - min_score) / (max_score - min_score + 1e-9) * 40 - 20  # 映射回 [-20, 20]
        mapped[k] = round(40 + 60 * norm.cdf(normed / sigma), 1)
    return mapped


# === 生成两个版本的六维得分 ===
dim_scores_gamma = calculate_dimension_scores_gamma(palace_scores_corrected, gamma=1.3)
dim_scores_cdf = calculate_dimension_scores_cdf(palace_scores_corrected, mu=0, sigma=10)

# === 雷达图数据准备 ===
labels = list(dim_scores_gamma.keys())
values_gamma = list(dim_scores_gamma.values())
values_cdf = list(dim_scores_cdf.values())

# 收尾闭合
values_gamma += values_gamma[:1]
values_cdf += values_cdf[:1]
angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
angles += angles[:1]

# === 绘图 ===
fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))

# Gamma 曲线
ax.plot(angles, values_gamma, marker='o', linewidth=2, color='#c19a6b', label='Gamma Mapping (γ=1.3)')
ax.fill(angles, values_gamma, alpha=0.3, color='#deb887')

# CDF 曲线
ax.plot(angles, values_cdf, marker='o', linewidth=2, color='#4682b4', label='Normal CDF Mapping (μ=0, σ=10)')
ax.fill(angles, values_cdf, alpha=0.2, color='#87cefa')

# 视觉配置
ax.set_xticks(angles[:-1])
ax.set_xticklabels(labels, fontsize=10)
ax.set_title("6D Personality Radar — Gamma vs Normal CDF Mapping", size=13, pad=20)
ax.spines['polar'].set_color('#8b7355')
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
plt.show()