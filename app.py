import streamlit as st
import numpy as np
import scipy.stats as stats
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional

# --- Configuration & Styling ---
st.set_page_config(
    page_title="Gender Bias ROI Simulator",
    page_icon="⚖️",
    layout="wide"
)

# Custom CSS for Branding Footer
st.markdown("""
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f0f2f6;
        color: #333;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        z-index: 999;
        border-top: 1px solid #ddd;
    }
    .footer a {
        color: #0366d6;
        text-decoration: none;
        font-weight: bold;
    }
    .main-content {
        margin-bottom: 60px; /* Footer space */
    }
    </style>
""", unsafe_allow_html=True)

# --- Logic Core: Hiring Model ---

class HiringSimulation:
    """
    労働市場における採用プロセスとバイアスの影響をシミュレートするクラス。
    レポート内の「3.1 選択効率性モデル」および「A.1 シミュレーションの前提条件」に基づく。
    """
    
    def __init__(self, mu_f: float, mu_m: float, sigma: float, threshold_fair: float):
        """
        Args:
            mu_f (float): 女性候補者の平均能力
            mu_m (float): 男性候補者の平均能力
            sigma (float): 能力分布の標準偏差（男女共通と仮定）
            threshold_fair (float): 公正な採用基準値 (T*)
        """
        self.mu_f = mu_f
        self.mu_m = mu_m
        self.sigma = sigma
        self.threshold_fair = threshold_fair

    def _calculate_truncated_stats(self, mu: float, threshold: float) -> tuple[float, float]:
        """
        切断正規分布の統計量を計算する（逆ミルズ比を使用）。
        Returns:
            (acceptance_rate, expected_value)
        """
        alpha = (threshold - mu) / self.sigma
        
        # 累積分布関数 (CDF) と 確率密度関数 (PDF)
        cdf = stats.norm.cdf(alpha)
        pdf = stats.norm.pdf(alpha)
        
        rate = 1 - cdf
        
        # ゼロ除算回避 (Error Handling)
        if rate <= 1e-9:
            return 0.0, 0.0
            
        # E[X|X>T] = mu + sigma * (pdf / (1-cdf))
        lambda_val = pdf / rate
        expected_val = mu + self.sigma * lambda_val
        
        return rate, expected_val

    def run(self, gamma_range: List[float], scenario_name: str, applicant_ratio_m: float = 0.5) -> pd.DataFrame:
        """
        指定されたバイアス範囲でシミュレーションを実行する。
        
        Args:
            gamma_range: バイアス係数のリスト
            scenario_name: シナリオ名
            applicant_ratio_m: 応募者プールにおける男性の割合 (0.0 - 1.0). Default 0.5.
        """
        results = []
        applicant_ratio_f = 1.0 - applicant_ratio_m
        
        for gamma in gamma_range:
            # 男性基準のみ引き下げ (T_M = T* - gamma)
            threshold_male = self.threshold_fair - gamma
            threshold_female = self.threshold_fair # 女性基準は固定

            # 女性の統計 (Biasなし)
            rate_f, avg_f = self._calculate_truncated_stats(self.mu_f, threshold_female)
            
            # 男性の統計 (Biasあり)
            rate_m, avg_m = self._calculate_truncated_stats(self.mu_m, threshold_male)
            
            # --- 組織全体の集計（母集団の比率を考慮） ---
            # 実際の採用数(比率) = 応募者割合 * 合格率
            hires_m = applicant_ratio_m * rate_m
            hires_f = applicant_ratio_f * rate_f
            total_hires = hires_m + hires_f
            
            if total_hires > 0:
                share_m = hires_m / total_hires
                # 加重平均による組織能力 (Organizational IQ)
                avg_total = (avg_m * hires_m + avg_f * hires_f) / total_hires
            else:
                share_m = 0.0
                avg_total = 0.0
            
            results.append({
                "Scenario": scenario_name,
                "Bias_Gamma": gamma,
                "Org_Avg_Ability": avg_total,
                "Male_Share": share_m,
                "Male_Avg_Ability": avg_m,
                "Female_Avg_Ability": avg_f,
                "Male_Threshold": threshold_male
            })
            
        return pd.DataFrame(results)

# --- Streamlit UI ---

def main():
    st.title("⚖️ Gender Bias ROI Simulator")
    st.markdown("""
    **採用バイアスが組織パフォーマンスに与える経済的損失（ROI悪化）の推計**
    
    本シミュレーターは、採用基準における「男性優遇バイアス（下駄）」が、組織全体の平均能力（生産性）と
    ジェンダー構成比にどのような構造的変化をもたらすかを数理的に検証します。
    """)

    # --- Sidebar: Parameters ---
    st.sidebar.header("🔧 Simulation Parameters")
    
    st.sidebar.subheader("1. 採用基準の設定")
    threshold_fair = st.sidebar.slider("公正な合格基準 (T*)", 0.5, 1.0, 0.75, 0.05, 
                                     help="正規分布上の偏差値に相当。0.75は約上位16%選抜を意味します。")
    sigma = st.sidebar.number_input("能力のばらつき (σ)", 0.1, 0.3, 0.15, 0.01)

    st.sidebar.subheader("2. 市場供給バランス (Supply)")
    applicant_ratio_m = st.sidebar.slider("応募者の男性比率", 0.0, 1.0, 0.5, 0.05, 
                                        help="市場における候補者プールの男女比（パイプライン問題の反映）")

    st.sidebar.markdown("---")
    st.sidebar.subheader("3. シナリオごとの能力仮定")
    
    # Scenario A
    with st.sidebar.expander("Scenario A: Ideal World (設定)", expanded=False):
        st.caption("男女の能力差が完全にない理想的な状態")
        mu_eq_f = st.number_input("SceA: 女性平均 (μF)", 0.0, 1.0, 0.60, 0.05, key="eq_f")
        mu_eq_m = st.number_input("SceA: 男性平均 (μM)", 0.0, 1.0, 0.60, 0.05, key="eq_m")

    # Scenario B
    with st.sidebar.expander("Scenario B: Pew Data (設定)", expanded=True):
        st.caption("高学歴化により供給側で女性が優位な現実")
        mu_pew_f = st.number_input("SceB: 女性平均 (μF)", 0.0, 1.0, 0.65, 0.05, key="pew_f")
        mu_pew_m = st.number_input("SceB: 男性平均 (μM)", 0.0, 1.0, 0.55, 0.05, key="pew_m")

    st.sidebar.markdown("---")
    max_gamma = st.sidebar.slider("最大バイアス係数 (Max Gamma)", 0.1, 0.5, 0.2, 0.05,
                                help="男性基準を最大でどれだけ引き下げるか（0.1 = 偏差値にして約-6.7ポイント相当）")

    # --- Execution ---
    gamma_values = np.linspace(0.0, max_gamma, 21)

    # Simulation 1: Equal Ability
    sim_equal = HiringSimulation(mu_f=mu_eq_f, mu_m=mu_eq_m, sigma=sigma, threshold_fair=threshold_fair)
    df_equal = sim_equal.run(gamma_values, "Scenario A: Equal Ability", applicant_ratio_m=applicant_ratio_m)

    # Simulation 2: Pew Data
    sim_pew = HiringSimulation(mu_f=mu_pew_f, mu_m=mu_pew_m, sigma=sigma, threshold_fair=threshold_fair)
    df_pew = sim_pew.run(gamma_values, "Scenario B: Pew Data (Reality)", applicant_ratio_m=applicant_ratio_m)

    # Combine Data
    df_combined = pd.concat([df_equal, df_pew])

    # --- Visualization ---
    st.subheader("📊 Simulation Results")
    
    col1, col2 = st.columns(2)
    
    # Plot Style Settings
    sns.set_style("whitegrid")
    colors = {"Scenario A: Equal Ability": "tab:blue", "Scenario B: Pew Data (Reality)": "tab:orange"}

    with col1:
        st.markdown("##### 📉 組織の平均能力 (Organizational IQ)")
        fig1, ax1 = plt.subplots(figsize=(6, 4))
        sns.lineplot(data=df_combined, x="Bias_Gamma", y="Org_Avg_Ability", 
                     hue="Scenario", palette=colors, style="Scenario", markers=True, ax=ax1, linewidth=2)
        ax1.set_xlabel("Bias (Gamma): Reduction in Male Standard")
        ax1.set_ylabel("Average Ability")
        ax1.set_title("Degradation of Org Productivity")
        st.pyplot(fig1)
        st.caption("バイアス（横軸）が強まるほど、組織IQ（縦軸）が低下する様子。")

    with col2:
        st.markdown("##### 📈 組織内の男性比率 (Male Share)")
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        sns.lineplot(data=df_combined, x="Bias_Gamma", y="Male_Share", 
                     hue="Scenario", palette=colors, style="Scenario", markers=True, ax=ax2, linewidth=2)
        # 応募者比率を点線で表示（これが「自然な状態」）
        ax2.axhline(applicant_ratio_m, color='green', linestyle=':', alpha=0.7, label="Applicant Ratio (Supply)")
        ax2.axhline(0.5, color='gray', linestyle='--', alpha=0.5, label="50% Parity")
        
        ax2.set_xlabel("Bias (Gamma): Reduction in Male Standard")
        ax2.set_ylabel("Male Share (Ratio)")
        ax2.set_ylim(0, 1.0)
        ax2.set_title("Rise of Male Dominance")
        ax2.legend()
        st.pyplot(fig2)
        st.caption(f"緑点線は応募者の男性比率（{applicant_ratio_m:.0%}）。ここから乖離して男性比率が上がるほど、採用基準が歪んでいることを示す。")

    # --- Data Table & Insights ---
    st.markdown("---")
    st.subheader("📋 Key Metrics Summary")
    
    st.markdown("バイアス最大時 (Max Gamma) と公正時 (Zero Bias) の比較")
    
    cols_to_show = ["Scenario", "Bias_Gamma", "Org_Avg_Ability", "Male_Share", "Productivity Gap"]
    # Add Productivity Gap calculation
    df_combined["Productivity Gap"] = df_combined["Female_Avg_Ability"] - df_combined["Male_Avg_Ability"]
    
    # Filter for display (0.0, mid, max)
    mid_gamma = round(max_gamma / 2, 2)
    filter_mask = df_combined["Bias_Gamma"].round(2).isin([0.0, mid_gamma, round(max_gamma, 2)])
    
    st.dataframe(df_combined[filter_mask][cols_to_show].style.format({
        "Bias_Gamma": "{:.2f}",
        "Org_Avg_Ability": "{:.3f}",
        "Male_Share": "{:.1%}",
        "Productivity Gap": "{:.3f}"
    }))

    # 動的なインサイト生成
    base_male_share_pew = df_pew[df_pew["Bias_Gamma"]==0.0]["Male_Share"].values[0]
    
    st.info(f"""
    **💡 分析のインサイト:**
    - **パイプラインの影響:** 応募者の男性比率を {applicant_ratio_m:.0%} に設定しています。
    - **公正採用時の結果:** Scenario B (現実) において、公正な採用を行うと、組織内の男性比率は **{base_male_share_pew:.1%}** となります。
    - **経営リスク:** もし、この状態で「男性比率 50%」や「応募比率並みの {applicant_ratio_m:.0%}」を目指してバイアスをかけると、
      その差分を埋めるために大量の「基準以下の候補者」を採用することになり、組織IQの劣化（グラフ左）が加速します。
    """)

    # --- Footer ---
    st.markdown("""
        <div class="footer">
            Created by: Keisuke Nakamura | 
            <a href="https://github.com/keisuke-data-lab" target="_blank">GitHub: https://github.com/keisuke-data-lab</a>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()