import streamlit as st
import numpy as np
import scipy.stats as stats
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional

# ==========================================
# 0. Page Config & Styling
# ==========================================
st.set_page_config(
    page_title="Gender Bias ROI Simulator",
    page_icon="⚖️",
    layout="wide"
)

# Custom CSS: Footer, Metrics, and Peak Highlight
st.markdown("""
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f8f9fa;
        color: #6c757d;
        text-align: center;
        padding: 10px;
        font-size: 12px;
        z-index: 999;
        border-top: 1px solid #ddd;
    }
    .disclaimer {
        font-size: 12px;
        color: #666;
        margin-top: 40px;
        padding: 15px;
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        border-radius: 4px;
    }
    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 24px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 1. Logic Class: Hiring Simulation
# ==========================================
class HiringSimulation:
    def __init__(self, mu_f: float, mu_m: float, sigma: float, threshold_fair: float):
        self.mu_f = mu_f
        self.mu_m = mu_m
        self.sigma = sigma
        self.threshold_fair = threshold_fair

    def _calculate_truncated_stats(self, mu: float, threshold: float) -> tuple[float, float]:
        """切断正規分布の統計量（合格率と合格者の平均能力）を計算"""
        alpha = (threshold - mu) / self.sigma
        cdf = stats.norm.cdf(alpha)
        pdf = stats.norm.pdf(alpha)
        rate = 1 - cdf
        
        if rate <= 1e-9:
            return 0.0, 0.0
            
        lambda_val = pdf / rate
        expected_val = mu + self.sigma * lambda_val
        return rate, expected_val

    def run(self, gamma_range: np.ndarray, scenario_name: str, applicant_ratio_m: float = 0.5) -> pd.DataFrame:
        results = []
        applicant_ratio_f = 1.0 - applicant_ratio_m
        
        for gamma in gamma_range:
            # Gamma > 0: 男性基準を下げる（優遇） -> Threshold下がる
            # Gamma < 0: 男性基準を上げる（厳格化/女性優先） -> Threshold上がる
            threshold_male = self.threshold_fair - gamma
            threshold_female = self.threshold_fair
            
            rate_f, avg_f = self._calculate_truncated_stats(self.mu_f, threshold_female)
            rate_m, avg_m = self._calculate_truncated_stats(self.mu_m, threshold_male)
            
            hires_m = applicant_ratio_m * rate_m
            hires_f = applicant_ratio_f * rate_f
            total_hires = hires_m + hires_f
            
            if total_hires > 0:
                share_m = hires_m / total_hires
                avg_total = (avg_m * hires_m + avg_f * hires_f) / total_hires
            else:
                share_m = 0.0
                avg_total = 0.0
            
            results.append({
                "Scenario": scenario_name,
                "Bias_Gamma": gamma,
                "Org_Avg_Ability": avg_total,
                "Male_Share": share_m,
                "Total_Hires_Rate": total_hires, # 採用数（率）も記録
                "Male_Avg_Ability": avg_m,
                "Female_Avg_Ability": avg_f
            })
            
        return pd.DataFrame(results)

# ==========================================
# 2. Financial & Analysis Functions
# ==========================================
def render_financial_sidebar():
    st.sidebar.markdown("---")
    st.sidebar.subheader("💰 Financial Impact Settings")
    
    employee_count = st.sidebar.number_input(
        "Total Employees (従業員数)", min_value=10, value=100, step=10
    )
    revenue_per_emp = st.sidebar.number_input(
        "Revenue per Employee (1人あたり付加価値/年)", min_value=100, value=1500, step=100
    ) * 10000 
    cost_per_hire = st.sidebar.number_input(
        "Cost per Hire (採用・教育単価)", min_value=10, value=300, step=50
    ) * 10000

    return employee_count, revenue_per_emp, cost_per_hire

def calculate_financial_loss(df, employee_count, revenue_per_emp, cost_per_hire):
    processed_frames = []
    
    for scenario in df['Scenario'].unique():
        sub_df = df[df['Scenario'] == scenario].copy()
        
        # ベースライン（Bias=0/中立）の能力を取得
        base_row = sub_df[(sub_df['Bias_Gamma'] >= -0.01) & (sub_df['Bias_Gamma'] <= 0.01)]
        if base_row.empty:
            base_ability = sub_df.iloc[len(sub_df)//2]['Org_Avg_Ability'] # フェイルセーフ
        else:
            base_ability = base_row.iloc[0]['Org_Avg_Ability']

        # 1. 機会損失 (Performance Drop)
        # Abilityが上がれば (Drop < 0) -> Lossはマイナス（＝利益）になる
        sub_df['Performance_Drop_Ratio'] = 1 - (sub_df['Org_Avg_Ability'] / base_ability)
        sub_df['Loss_Opportunity'] = sub_df['Performance_Drop_Ratio'] * (revenue_per_emp * employee_count)

        # 2. 採用浪費 (Sunk Cost)
        wasted_ratio = sub_df['Performance_Drop_Ratio'].clip(lower=0)
        sub_df['Loss_SunkCost'] = wasted_ratio * (cost_per_hire * employee_count)

        # 3. 総損失
        sub_df['Total_Loss'] = sub_df['Loss_Opportunity'] + sub_df['Loss_SunkCost']
        
        processed_frames.append(sub_df)
    
    return pd.concat(processed_frames)

def analyze_peak_performance(df, scenario_name):
    """指定シナリオにおける最適解（損失最小点）を見つける"""
    target_df = df[df['Scenario'] == scenario_name]
    if target_df.empty: return None, None, None
    
    # Total_Loss が最小（＝利益最大）の行
    best_row_idx = target_df['Total_Loss'].idxmin()
    best_row = target_df.loc[best_row_idx]
    
    best_gamma = best_row['Bias_Gamma']
    min_loss = best_row['Total_Loss']
    max_ability = best_row['Org_Avg_Ability']
    
    return best_gamma, min_loss, max_ability

# ==========================================
# 3. Main Application
# ==========================================
def main():
    st.title("⚖️ Gender Bias ROI Simulator: Optimization Engine")
    
    st.markdown("""
    **採用基準の最適化による組織パフォーマンス最大化シミュレーション**
    
    本ツールは、採用における「バイアス（基準の歪み）」が経済的損失をもたらすか、
    あるいは特定の戦略的バイアス（ポジティブ・アクション等）が組織IQを高めるかを数理的に特定します。
    """)

    # --- 1. Sidebar Parameters ---
    st.sidebar.header("🔧 Simulation Parameters")
    
    # 採用基準
    threshold_fair = st.sidebar.slider("公正な合格基準 (T*)", 0.5, 1.0, 0.75, 0.05,
                                     help="正規分布上の偏差値相当。0.75=上位約16%")
    sigma = 0.15 # 固定
    
    # 市場環境
    applicant_ratio_m = st.sidebar.slider("応募者の男性比率", 0.0, 1.0, 0.5, 0.05,
                                        help="候補者プールの男女比")

    # 財務設定
    employee_count, revenue_per_emp, cost_per_hire = render_financial_sidebar()

    st.sidebar.markdown("---")
    st.sidebar.subheader("3. シナリオ比較設定")
    
    # シナリオA: 平等
    with st.sidebar.expander("Scenario A: Equal Ability (Benchmark)", expanded=True):
        st.markdown("<small>男女の平均能力が完全に等しい理想状態</small>", unsafe_allow_html=True)
        mu_eq_f = 0.60
        mu_eq_m = 0.60

    # シナリオB: 研究データ (Reality/Research)
    with st.sidebar.expander("Scenario B: Research Case (Pew Data)", expanded=False):
        st.markdown("<small>女性の社会的スキル等がやや高いとする研究ケース</small>", unsafe_allow_html=True)
        mu_pew_f = st.slider("SceB: 女性平均", 0.0, 1.0, 0.65, 0.05)
        mu_pew_m = st.slider("SceB: 男性平均", 0.0, 1.0, 0.55, 0.05)

    st.sidebar.markdown("---")
    
    # 現在の立ち位置確認用スライダー
    current_gamma_input = st.sidebar.slider(
        "現在の想定バイアス (Current Status)", 
        min_value=-0.5, max_value=0.5, value=0.1, step=0.05,
        help="正(+): 男性優遇 / 負(-): 女性登用・実力重視"
    )

    # --- 2. Execution ---
    gamma_values = np.linspace(-0.5, 0.5, 101)

    sim_equal = HiringSimulation(mu_eq_f, mu_eq_m, sigma, threshold_fair)
    df_equal = sim_equal.run(gamma_values, "Scenario A: Equal Ability", applicant_ratio_m)

    sim_pew = HiringSimulation(mu_pew_f, mu_pew_m, sigma, threshold_fair)
    df_pew = sim_pew.run(gamma_values, "Scenario B: Research Case (Pew Data)", applicant_ratio_m)

    df_combined = pd.concat([df_equal, df_pew])
    df_final = calculate_financial_loss(df_combined, employee_count, revenue_per_emp, cost_per_hire)

    # --- 3. Dashboard ---
    st.subheader("📊 Optimization Dashboard")
    
    # ピーク分析
    opt_gamma, opt_loss, opt_ability = analyze_peak_performance(df_final, "Scenario B: Research Case (Pew Data)")
    
    # 現在地メトリクス
    def get_metrics_at_gamma(df, scenario, g):
        target = df[df['Scenario'] == scenario]
        row = target.iloc[(target['Bias_Gamma'] - g).abs().argsort()[:1]].iloc[0]
        return row

    current_row = get_metrics_at_gamma(df_final, "Scenario B: Research Case (Pew Data)", current_gamma_input)
    
    # Metrics Display
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current Bias", f"{current_gamma_input:.2f}", help="現在の設定値")
    
    with col2:
        val = current_row['Total_Loss']
        is_profit = val < 0
        label = "Estimated Impact"
        display_val = f"¥{abs(val)/100_000_000:,.1f} 億円"
        
        if is_profit:
            st.metric(label + " (Profit)", display_val, delta=f"+¥{abs(val):,.0f} Gain", delta_color="normal")
        else:
            st.metric(label + " (Loss)", display_val, delta=f"-¥{val:,.0f} Loss", delta_color="inverse")

    with col3:
        if opt_loss is not None:
            potential_gain = current_row['Total_Loss'] - opt_loss
            st.metric("Optimization Potential", f"¥{potential_gain/100_000_000:,.1f} 億円", 
                      help="バイアスを最適値に変更することで得られる追加利益", delta="Up is Good")
    
    with col4:
        st.metric("Optimal Bias Point", f"{opt_gamma:.2f}", 
                  help="組織利益が最大化するバイアス値", delta_color="off")

    st.markdown("---")

    # --- 4. Visualization ---
    tab1, tab2 = st.tabs(["📉 Profit/Loss Curve (Optimization)", "📈 Org Parameters"])
    
    colors = {"Scenario A: Equal Ability": "tab:blue", "Scenario B: Research Case (Pew Data)": "tab:orange"}

    with tab1:
        st.markdown("**💰 Financial Impact Landscape**")
        fig_fin, ax_fin = plt.subplots(figsize=(10, 6))
        
        ax_fin.axhline(0, color='black', linewidth=1, linestyle='-')
        sns.lineplot(data=df_final, x="Bias_Gamma", y=df_final["Total_Loss"]/100000000, 
                     hue="Scenario", palette=colors, style="Scenario", linewidth=2.5, ax=ax_fin)
        
        ax_fin.axvspan(-0.5, 0, color='blue', alpha=0.05, label="Strict Male Selection")
        ax_fin.axvspan(0, 0.5, color='red', alpha=0.05, label="Male Favoritism")
        
        if opt_gamma is not None and abs(opt_gamma) > 0.01:
            ax_fin.axvline(opt_gamma, color='green', linestyle='--', linewidth=2, label=f"Optimal: {opt_gamma:.2f}")
            ax_fin.plot(opt_gamma, opt_loss/100000000, 'go', markersize=10)

        ax_fin.axvline(current_gamma_input, color='gray', linestyle=':', linewidth=2, label="Current Position")

        ax_fin.set_xlabel("Bias Gamma (◀ Female Priority | Neutral | Male Priority ▶)")
        ax_fin.set_ylabel("Financial Impact (Low/Negative is Good) [100M JPY]")
        ax_fin.set_title("Profit Optimization Curve")
        ax_fin.legend()
        ax_fin.grid(True, linestyle='--', alpha=0.5)
        st.pyplot(fig_fin)
        
        if opt_loss < 0:
            msg_type = st.success
            msg_text = f"""
            **🧪 理論上の最大ポテンシャル (Theoretical Optimization Value):**
            Scenario Bの統計仮定に基づき計算すると、バイアス係数 **{opt_gamma:.2f}** （女性積極登用/男性厳格化）の地点で、
            組織ROIが数理的に最大化されるという試算結果となりました。
            
            これにより、公平時(0)と比較して **年間 {abs(opt_loss)/100000000:,.1f} 億円** の付加価値創出が理論上可能と算出されます。
            """
        else:
            msg_type = st.info
            msg_text = "**ℹ️ 分析結果:** Scenario A（能力均等）の仮定下では、バイアス **0.0 (公平)** が最も損失を最小化する数理的最適解となります。"
        msg_type(msg_text)

    # ---------------------------------------------------------
    # Tab 2: ここが修正されたナラティブ復活箇所です
    # ---------------------------------------------------------
    with tab2:
        col_a, col_b = st.columns(2)
        
        # --- 左側: 組織平均能力 ---
        with col_a:
            st.markdown("##### 🧠 Org Average Ability (組織IQ)")
            fig1, ax1 = plt.subplots(figsize=(6, 4))
            sns.lineplot(data=df_final, x="Bias_Gamma", y="Org_Avg_Ability", hue="Scenario", palette=colors, ax=ax1)
            ax1.set_xlabel("Bias Gamma")
            ax1.set_ylabel("Average Ability Score")
            ax1.axvline(0, color='gray', linestyle=':')
            st.pyplot(fig1)
            
            # 【復活】組織能力に関する鋭利な解説
            st.info("""
            **▼グラフの読み解き:**
            **左端（Bias=0）が組織IQの最大ポテンシャル（Potential Max）です。**
            ここから右へ進む（バイアスをかける）ことは、すべて経営資源の毀損を意味します。
            特に「Reality（オレンジ）」では、本来採用すべき優秀な女性を弾くため、劣化がより激しくなります。
            """)

        # --- 右側: 男性比率 ---
        with col_b:
            st.markdown("##### 👥 Male Share (男性比率)")
            fig2, ax2 = plt.subplots(figsize=(6, 4))
            sns.lineplot(data=df_final, x="Bias_Gamma", y="Male_Share", hue="Scenario", palette=colors, ax=ax2)
            
            # 参照ラインの描画
            ax2.axhline(applicant_ratio_m, color='green', linestyle=':', label=f"Applicant Ratio ({applicant_ratio_m:.0%})")
            ax2.axvline(0, color='gray', linestyle=':')
            ax2.set_xlabel("Bias Gamma")
            ax2.legend()
            st.pyplot(fig2)
            
            # 【復活】男性比率に関する冷徹な指摘
            st.warning(f"""
            **▼グラフの読み解き:**
            緑の点線（応募比率 {applicant_ratio_m:.0%}）や灰色の点線（50%）を超えて男性比率が上昇している領域は、
            **「統計的に能力不足の男性」が下駄を履いて流入している**ことを示唆します。
            「50%」を目指すことが目的化すると、組織の質は必然的に低下します。
            """)

    # --- Footer ---
    st.markdown("""
        <div class="disclaimer">
            **⚠️ 免責事項 (Optimization Model Disclaimer)**<br>
            本シミュレーションの「マイナス領域（女性登用/男性厳格化）」における利益算出は、
            「Scenario B（女性の平均能力が高い）」という特定の統計仮定に基づいた理論値です。
            実際の採用戦略においては、法的な公平性や組織のコンテキストを考慮する必要があります。
        </div>
        <div class="footer">
            Gender Bias ROI Simulator | © 2026 Keisuke Data Lab
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()