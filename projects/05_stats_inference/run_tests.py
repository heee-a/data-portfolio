"""统计推断实战：用城市气象数据做三个带完整流程的假设检验。

每个检验：H0/H1 -> 检验方法选择理由 -> 统计量/p值 -> 效应量 -> 结论 -> 局限。
数据: ../01_weather_cities/data/weather_daily.csv（18 城为样本单位）
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from datap.plotstyle import save_chart, setup_style

ROOT = Path(__file__).parent
CHARTS = ROOT / "charts"
LAT_DIVIDER = 33.0  # 南北分界纬度（秦岭-淮河≈33°N）
COASTAL = {"上海", "杭州", "广州", "深圳", "三亚"}


def cohen_d(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = len(a), len(b)
    sp = np.sqrt(((na - 1) * a.std(ddof=1) ** 2 + (nb - 1) * b.std(ddof=1) ** 2)
                 / (na + nb - 2))
    return (a.mean() - b.mean()) / sp


def bootstrap_ci_diff(a: np.ndarray, b: np.ndarray, n_boot: int = 10000,
                      seed: int = 42) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    diffs = [rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean()
             for _ in range(n_boot)]
    return tuple(np.percentile(diffs, [2.5, 97.5]))


def report(title: str, a: np.ndarray, b: np.ndarray,
           name_a: str, name_b: str) -> None:
    t, p_t = stats.ttest_ind(a, b, equal_var=False)
    u, p_u = stats.mannwhitneyu(a, b, alternative="two-sided")
    d = cohen_d(a, b)
    lo, hi = bootstrap_ci_diff(a, b)
    print(f"\n## {title}")
    print(f"  {name_a}(n={len(a)}): 均值 {a.mean():.1f} ± {a.std(ddof=1):.1f} | "
          f"{name_b}(n={len(b)}): 均值 {b.mean():.1f} ± {b.std(ddof=1):.1f}")
    print(f"  Welch t 检验: t={t:.2f}, p={p_t:.4f} | Mann-Whitney U: p={p_u:.4f}")
    print(f"  效应量 Cohen's d = {d:.2f}（{'大' if abs(d)>=0.8 else '中' if abs(d)>=0.5 else '小'}效应）")
    print(f"  均值差的 95% Bootstrap CI: [{lo:.1f}, {hi:.1f}]")
    sig = "拒绝 H0" if p_u < 0.05 else "不能拒绝 H0"
    print(f"  结论（α=0.05，以对分布假设更宽松的 Mann-Whitney 为准）：{sig}")


def main() -> None:
    setup_style()
    daily = pd.read_csv(Path(__file__).resolve().parents[1] / "01_weather_cities"
                        / "data" / "weather_daily.csv", parse_dates=["date"])
    daily["month"] = daily["date"].dt.month
    daily["lat"] = daily["city"].map({
        "哈尔滨": 45.8, "长春": 43.9, "乌鲁木齐": 43.8, "北京": 39.9, "兰州": 36.1,
        "郑州": 34.8, "西安": 34.3, "南京": 32.1, "上海": 31.2, "武汉": 30.6,
        "成都": 30.6, "重庆": 29.6, "杭州": 30.3, "拉萨": 29.7, "昆明": 25.0,
        "广州": 23.1, "深圳": 22.5, "三亚": 18.3})
    summer = (daily[daily["month"].isin([6, 7, 8])]
              .groupby("city").agg(precip=("precip", "sum"), lat=("lat", "first"))
              .reset_index())
    total = daily.groupby("city")["precip"].sum()
    summer["ratio"] = summer["precip"] / summer["city"].map(total) * 100

    north = summer[summer["lat"] >= LAT_DIVIDER]["ratio"].values
    south = summer[summer["lat"] < LAT_DIVIDER]["ratio"].values
    report("检验一：北方城市夏季降水占比是否更高？（秦岭-淮河 33°N 分组）",
           north, south, "北方", "南方")

    is_coastal = summer["city"].isin(COASTAL)
    coastal = summer[is_coastal]["precip"].values / 6  # 6 年均值口径
    inland = summer[~is_coastal]["precip"].values / 6
    report("检验二：沿海城市年降水量是否更高？", coastal, inland, "沿海", "内陆")

    # 检验三：昆明月均温波动是否显著小于其他城市（Levene 方差齐性检验）
    monthly = (daily.groupby(["city", "month"])["tmean"].mean()
               .reset_index().rename(columns={"tmean": "month_mean"}))
    km = monthly[monthly["city"] == "昆明"]["month_mean"].values
    others = monthly[monthly["city"] != "昆明"]["month_mean"].values
    w, p_w = stats.levene(km, others, center="median")
    print(f"\n## 检验三：昆明的气温波动是否显著更小？（「四季如春」的统计验证）")
    print(f"  昆明月均温标准差 {km.std(ddof=1):.1f}℃ vs 其他城市 "
          f"{others.std(ddof=1):.1f}℃")
    print(f"  Levene 检验: W={w:.2f}, p={p_w:.2e}")
    print(f"  结论（α=0.05）：{'拒绝 H0，昆明月均温方差显著更小，「四季如春」成立' if p_w < 0.05 else '不能拒绝 H0'}")

    # 图 1：南北夏季降水占比箱线
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.boxplot([north, south], tick_labels=[f"北方(n={len(north)})", f"南方(n={len(south)})"])
    ax.set_ylabel("夏季(6-8月)降水占比 %")
    ax.set_title(f"南北夏季降水占比差异：Mann-Whitney p={stats.mannwhitneyu(north, south)[1]:.3f}")
    save_chart(fig, CHARTS / "test1_north_south.png")

    # 图 2：沿海 vs 内陆年降水箱线
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.boxplot([coastal, inland], tick_labels=[f"沿海(n={len(coastal)})", f"内陆(n={len(inland)})"])
    ax.set_ylabel("年均降水 mm")
    ax.set_title(f"沿海 vs 内陆年降水：Mann-Whitney p={stats.mannwhitneyu(coastal, inland)[1]:.3f}")
    save_chart(fig, CHARTS / "test2_coastal_inland.png")

    # 图 3：月均温波动对比
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(others, bins=24, alpha=0.6, label="其他 17 城月均温", color="#4C72B0")
    ax.hist(km, bins=12, alpha=0.75, label="昆明月均温", color="#C44E52")
    ax.set_xlabel("月均温 ℃")
    ax.set_ylabel("月份数")
    ax.set_title(f"「四季如春」的统计验证：Levene p={p_w:.1e}")
    ax.legend()
    save_chart(fig, CHARTS / "test3_kunming.png")
    print(f"\n图表已输出 -> {CHARTS}/")
    print("\n局限：样本单位是『城市』而非『天』（n=18，避免伪重复）；"
          "三个检验构成多重比较，若需严格可做 Bonferroni 校正（α=0.017）。")


if __name__ == "__main__":
    main()
