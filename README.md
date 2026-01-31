# ⚖️ Gender Bias ROI & Optimization Engine
**組織パフォーマンスを最大化する「採用基準の黄金比」を特定する数理監査モデル**

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://gender-bias-simulation-efntmryjj8pth6vr86vpwn.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

<br>

![Demo Animation](demo_simulation.gif)
*(The simulation visualizes how shifting hiring standards directly impacts financial ROI based on truncated normal distribution models.)*

<br>

## 📌 Executive Summary
**「現状維持（Status Quo）」は、年間いくらの損失を生んでいるか？**

多くの企業において、採用基準のバイアス（性別役割分担意識による下駄やフィルタリング）は「道徳的問題」として処理されています。しかし、経営視点においてそれは**「人的資本ROIの毀損（Financial Loss）」**に他なりません。

本エンジンは、採用プロセスにおけるバイアスと市場供給（パイプライン）の関係を統計的にモデル化し、**組織の平均能力（Organizational IQ）と経済的損失**を定量化します。さらに、単なる損失計算に留まらず、組織パフォーマンスが数学的に最大化される**「最適化ポイント（Optimization Point）」**を特定します。

### 🚀 Business Value
1.  **Invisible Loss Quantification (見えない損失の可視化):**
    「なんとなく男性を採用する」慣習が、機会損失（Opportunity Loss）と採用浪費（Sunk Cost）として財務諸表にどう影響しているかを円換算で算出。
2.  **Peak Performance Detection (最適解の発見):**
    「平等（バイアス0）」がゴールとは限りません。統計的仮定（Scenario B）に基づき、組織利益が最大化される**戦略的採用基準（Theoretical Optimum）**を提示します。
3.  **Strict Mathematical Audit (冷徹な数理監査):**
    感情論を排除し、正規分布と統計確率のみに基づいた客観的なシミュレーションを提供します。

---

## 📊 Simulation Logic & Scenarios

本モデルでは、以下の2つの世界観（仮定）における財務インパクトを比較検証します。

| Scenario | 概要 | 統計的仮定 (Statistical Assumption) |
| :--- | :--- | :--- |
| **A. Equal Ability** | **理想的ベンチマーク** | 男女の能力分布に差がない完全な均質状態。<br>($\mu_F = \mu_M$) |
| **B. Research Case** | **現実のデータ** | Pew Research Center等の調査に基づき、非認知能力や学歴において女性がやや高いスコアを持つケースを想定。<br>($\mu_F > \mu_M$) |

### 🛠 Mathematical Framework
本シミュレーションは、**切断正規分布 (Truncated Normal Distribution)** の統計的性質を利用しています。

1.  **能力評価:** 候補者の能力 $X \sim N(\mu, \sigma^2)$ に対し、閾値 $T$ を超えた者を採用。
2.  **バイアス操作:** $\gamma$ (Gamma) を調整変数とし、特定の性別に対する基準の緩和・厳格化をシミュレート。
    $$T_{biased} = T_{fair} - \gamma$$
3.  **ROI計算:** 採用された人材の期待能力値 $E[X|X>T]$ の変動を、従業員一人当たりの付加価値（Revenue per Employee）に換算して算出。

---

## 📉 Optimization Landscape
本ツールは、「損失（Loss）」だけでなく「利益（Gain）」の可能性も探索します。

* **Right Side (Gamma > 0): Male Favoritism**
    男性基準を引き下げる領域。能力密度の低下により、指数関数的に損失が拡大します。
* **Center (Gamma = 0): Neutral**
    完全な実力主義。Scenario Aにおいてはここが最適解となります。
* **Left Side (Gamma < 0): Strategic Optimization**
    男性基準を厳格化（または女性を積極登用）する領域。Scenario Bの仮定下では、**この領域に組織ROIの最大値（Peak）が存在する可能性**があります。

---

## 💻 How to Run Locally

```bash
# 1. Clone the repository
git clone [https://github.com/keisuke-data-lab/gender-bias-simulation.git](https://github.com/keisuke-data-lab/gender-bias-simulation.git)
cd gender-bias-simulation

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
streamlit run app.py