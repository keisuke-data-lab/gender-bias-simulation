import numpy as np
import scipy.stats as stats
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 出力ディレクトリの設定
OUTPUT_DIR = "results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# グラフスタイルの設定
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

def calculate_metrics(mu_f, mu_m, sigma, threshold_fair, gamma_values, label):
    """
    指定されたパラメータに基づいて採用バイアスのシミュレーションを行う関数
    """
    results = []
    
    for gamma in gamma_values:
        # 男性基準のみを引き下げる (バイアス適用: T_M = T* - gamma)
        threshold_male = threshold_fair - gamma
        threshold_female = threshold_fair # 女性基準は公正なまま固定
        
        # --- 女性 (Female) ---
        alpha_f = (threshold_female - mu_f) / sigma
        rate_f = 1 - stats.norm.cdf(alpha_f)
        # 切断正規分布の期待値計算 (逆ミルズ比)
        if rate_f > 0:
            lambda_f = stats.norm.pdf(alpha_f) / rate_f
            avg_ability_f = mu_f + sigma * lambda_f
        else:
            avg_ability_f = 0 # 理論上ありえないがゼロ除算回避
        
        # --- 男性 (Male) ---
        alpha_m = (threshold_male - mu_m) / sigma
        rate_m = 1 - stats.norm.cdf(alpha_m)
        if rate_m > 0:
            lambda_m = stats.norm.pdf(alpha_m) / rate_m
            avg_ability_m = mu_m + sigma * lambda_m
        else:
            avg_ability_m = 0

        # --- 組織全体 (Organization) ---
        # 応募者プールが男女同数(50:50)であると仮定
        total_hires = rate_m + rate_f
        if total_hires > 0:
            share_m = rate_m / total_hires
            share_f = rate_f / total_hires
            avg_ability_total = (avg_ability_m * rate_m + avg_ability_f * rate_f) / total_hires
        else:
            share_m, share_f, avg_ability_total = 0, 0, 0
        
        results.append({
            "Scenario": label,
            "Bias_Gamma": gamma,
            "Male_Threshold": round(threshold_male, 3),
            "Org_Avg_Ability": avg_ability_total,
            "Male_Share": share_m,
            "Male_Avg_Ability": avg_ability_m,
            "Female_Avg_Ability": avg_ability_f
        })
    return pd.DataFrame(results)

def main():
    # 共通パラメータ
    SIGMA_COMMON = 0.15
    THRESHOLD_FAIR = 0.75 # 上位約16% (1シグマ)
    GAMMA_RANGE = np.linspace(0.00, 0.20, 21) # バイアス範囲

    # --- シナリオ1: 能力差なし (Equal Ability) ---
    print("Running Scenario 1: Equal Ability...")
    df_equal = calculate_metrics(
        mu_f=0.60, mu_m=0.60, sigma=SIGMA_COMMON, 
        threshold_fair=THRESHOLD_FAIR, gamma_values=GAMMA_RANGE, 
        label="Equal Ability (μF=μM)"
    )

    # --- シナリオ2: 現実データ反映 (Pew Data / Female Advantage) ---
    print("Running Scenario 2: Pew Data (Female Advantage)...")
    df_pew = calculate_metrics(
        mu_f=0.65, mu_m=0.55, sigma=SIGMA_COMMON, 
        threshold_fair=THRESHOLD_FAIR, gamma_values=GAMMA_RANGE, 
        label="Pew Data (μF>μM)"
    )

    # 結合
    df_comparison = pd.concat([df_equal, df_pew])
    
    # --- 結果の保存 ---
    csv_path = f"{OUTPUT_DIR}/simulation_results.csv"
    df_comparison.to_csv(csv_path, index=False)
    print(f"Data saved to {csv_path}")

    # --- 可視化 ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # グラフ1: 組織生産性
    sns.lineplot(data=df_comparison, x="Bias_Gamma", y="Org_Avg_Ability", 
                hue="Scenario", style="Scenario", markers=True, ax=ax1, linewidth=2.5)
    ax1.set_title("Degradation of Org Productivity: Impact of Bias")
    ax1.set_xlabel("Bias (gamma): Reduction in Male Standard")
    ax1.set_ylabel("Average Ability of Organization")
    ax1.grid(True)

    # グラフ2: 男性比率
    sns.lineplot(data=df_comparison, x="Bias_Gamma", y="Male_Share", 
                hue="Scenario", style="Scenario", markers=True, ax=ax2, linewidth=2.5)
    ax2.set_title("Rise of Male Dominance: Impact of Bias")
    ax2.set_xlabel("Bias (gamma): Reduction in Male Standard")
    ax2.set_ylabel("Male Share in Hires")
    ax2.axhline(0.5, color='gray', linestyle='--', label='50% Parity')
    ax2.set_ylim(0, 1.0)
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    img_path = f"{OUTPUT_DIR}/comparison_plot.png"
    plt.savefig(img_path)
    print(f"Plot saved to {img_path}")

if __name__ == "__main__":
    main()