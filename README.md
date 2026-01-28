# ⚖️ Gender Bias ROI Simulator
**採用バイアスがもたらす「組織IQの損失」と「ダイバーシティの罠」を定量化する数理モデル**

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://gender-bias-simulation-efntmryjj8pth6vr86vpwn.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## 📌 Executive Summary
**「女性の応募が少ないから、男性ばかり採用するのは仕方ない」は、数学的に正しいか？**

このシミュレーターは、採用プロセスにおける**「バイアス（下駄）」**と**「市場のパイプライン（応募者比率）」**の関係をモデル化し、無理なジェンダー比率調整が組織の**平均能力（Organizational IQ）**に与える経済的損失を算出します。

### 🚀 Key Insights
1.  **バイアスの代償 (The Cost of Bias):**
    男性比率を維持するために採用基準を引き下げると、組織全体の生産性は急激に低下する。
2.  **パイプラインの真実 (Pipeline Reality):**
    たとえ応募者の8割が男性であっても、女性の基礎能力が高い（Pew Researchシナリオ）場合、公正な採用を行えば女性採用比率は応募比率（2割）を上回る。
3.  **見えない損失 (Invisible Loss):**
    現状維持（男性優位）のために支払っている「生産性ギャップ」を数値化し、経営リスクとして提示する。

---

## 📊 Simulation Scenarios

本モデルでは、以下の2つの世界を比較検証します。

| Scenario | 概要 | 前提条件 |
| :--- | :--- | :--- |
| **A. Equal Ability** | **理想的な世界** | 男女の能力分布に差がない完全な平等状態。<br>(μ_F = μ_M) |
| **B. Pew Data (Reality)** | **現実のデータ** | 先進国の若年層において、女性の方が高学歴（能力スコアが高い）である傾向を反映。<br>(μ_F > μ_M) |

---

## 🛠 Model Logic (Mathematical Framework)

本シミュレーションは、**切断正規分布 (Truncated Normal Distribution)** の統計的性質を利用しています。

### 1. 採用プロセス
応募者の能力 $X$ は正規分布 $N(\mu, \sigma^2)$ に従うとし、閾値 $T$ を超えた候補者を採用します。採用者の平均能力 $E[X|X>T]$ は**逆ミルズ比**を用いて算出されます。

### 2. バイアスの定義 ($\gamma$)
男性の採用基準のみを $\gamma$ (Gamma) だけ引き下げる操作を「バイアス」と定義します。
$$Threshold_{Male} = Threshold_{Fair} - \gamma$$

### 3. パイプライン（供給）の考慮
市場における応募者の男性比率 ($r_m$) を変数として組み込み、最終的な組織構成比をベイズ的に算出します。
$$Share_{Male} = \frac{r_m \cdot Rate_{Male}}{r_m \cdot Rate_{Male} + (1-r_m) \cdot Rate_{Female}}$$

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
