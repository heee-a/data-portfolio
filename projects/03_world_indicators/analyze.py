"""分析世界发展指标：中国 20 余年变迁、收入与预期寿命的关系、国家对比。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import matplotlib.pyplot as plt
import pandas as pd

from datap.plotstyle import save_chart, setup_style

ROOT = Path(__file__).parent
CHARTS = ROOT / "charts"
LATEST = 2023


def load() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "data" / "indicators_long.csv")
    return df.pivot_table(index=["country_id", "country", "year"],
                          columns="indicator_name", values="value") \
             .reset_index().rename(columns={
                 "人均GDP美元": "gdp_pc", "预期寿命": "life_exp",
                 "人均CO2吨": "co2_pc", "城市化率%": "urban"})


def chart_china(df: pd.DataFrame) -> Path:
    setup_style()
    cn = df[(df["country_id"] == "CHN") & (df["year"] >= 2000)].sort_values("year")
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(cn["year"], cn["gdp_pc"], marker="o", ms=4, color="#C44E52",
             label="人均GDP（左轴）")
    ax1.set_ylabel("人均GDP 美元")
    ax2 = ax1.twinx()
    ax2.plot(cn["year"], cn["urban"], marker="s", ms=3, color="#4C72B0",
             label="城市化率（右轴）")
    ax2.plot(cn["year"], cn["life_exp"], marker="^", ms=3, color="#55A868",
             label="预期寿命（右轴）")
    ax2.set_ylabel("城市化率 % / 预期寿命 岁")
    ax2.grid(False)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left")
    ax1.set_title("中国 2000-2023：人均GDP 与城市化、预期寿命同步跃升")
    return save_chart(fig, CHARTS / "china_2000_2023.png")


def chart_income_life(df: pd.DataFrame) -> Path:
    setup_style()
    d = df[df["year"] == LATEST].dropna(subset=["gdp_pc", "life_exp"])
    big = {"CHN", "USA", "IND", "JPN", "DEU", "BRA", "RUS", "NGA", "IDN", "KOR"}
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.scatter(d["gdp_pc"], d["life_exp"], s=22, alpha=0.55,
               c="#4C72B0", edgecolors="none")
    for cid in big:
        row = d[d["country_id"] == cid]
        if len(row):
            r = row.iloc[0]
            ax.scatter(r["gdp_pc"], r["life_exp"], s=70, c="#C44E52", zorder=5)
            ax.annotate(r["country"], (r["gdp_pc"], r["life_exp"]), fontsize=9,
                        xytext=(4, 4), textcoords="offset points")
    ax.set_xscale("log")
    corr = d[["gdp_pc", "life_exp"]].corr().iloc[0, 1]
    ax.set_xlabel(f"人均GDP 美元（log）—— 与预期寿命相关系数 {corr:.2f}")
    ax.set_ylabel("预期寿命 岁")
    ax.set_title(f"{LATEST} 年收入与预期寿命：经典的 Preston 曲线")
    return save_chart(fig, CHARTS / "income_life.png")


def chart_compare(df: pd.DataFrame) -> Path:
    setup_style()
    picks = {"CHN": "中国", "USA": "美国", "JPN": "日本", "KOR": "韩国",
             "IND": "印度", "BRA": "巴西"}
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for cid, name in picks.items():
        d = df[(df["country_id"] == cid) & (df["year"] >= 2000)].sort_values("year")
        if not len(d):
            continue
        axes[0].plot(d["year"], d["gdp_pc"], marker=".", ms=3, label=name)
        axes[1].plot(d["year"], d["urban"], marker=".", ms=3, label=name)
    axes[0].set_title("人均GDP（2000-2023）")
    axes[0].set_ylabel("美元")
    axes[1].set_title("城市化率（2000-2023）")
    axes[1].set_ylabel("%")
    for ax in axes:
        ax.legend(fontsize=9)
    return save_chart(fig, CHARTS / "country_compare.png")


def main() -> None:
    df = load()
    cn = df[(df["country_id"] == "CHN") & df["year"].isin([2000, LATEST])]
    cn2000 = cn[cn["year"] == 2000].iloc[0]
    cn23 = cn[cn["year"] == LATEST].iloc[0]
    d23 = df[df["year"] == LATEST].dropna(subset=["gdp_pc"])

    print(f"数据: {len(df):,} 行, {df['country_id'].nunique()} 国家/地区, "
          f"{df['year'].min()}-{df['year'].max()}")
    print("\n=== 关键发现（供 README 引用）===")
    print(f"1. 中国人均GDP {cn2000['gdp_pc']:,.0f} -> {cn23['gdp_pc']:,.0f} 美元 "
          f"（{cn23['gdp_pc']/cn2000['gdp_pc']:.1f}×），同期城市化率 "
          f"{cn2000['urban']:.0f}% -> {cn23['urban']:.0f}%，预期寿命 "
          f"{cn2000['life_exp']:.1f} -> {cn23['life_exp']:.1f} 岁")
    rank = (d23["gdp_pc"].rank(ascending=False)[d23["country_id"] == "CHN"]).iloc[0]
    print(f"2. {LATEST} 年中国人均GDP 全球排名 {int(rank)}/{len(d23)}；"
          f"全球中位数 {d23['gdp_pc'].median():,.0f} 美元")
    corr = d23[["gdp_pc", "life_exp"]].corr().iloc[0, 1]
    corr_c = d23[["gdp_pc", "life_exp"]].corr(method="spearman").iloc[0, 1]
    print(f"3. 收入与预期寿命 Pearson r={corr:.2f}（Spearman {corr_c:.2f}，取对数后更接近线性）")
    cn_co2 = df[(df["country_id"] == "CHN") & (df["year"] == LATEST)]["co2_pc"]
    usa_co2 = df[(df["country_id"] == "USA") & (df["year"] == LATEST)]["co2_pc"]
    if len(cn_co2) and len(usa_co2):
        print(f"4. 人均CO2: 中国 {cn_co2.iloc[0]:.1f} 吨 vs 美国 {usa_co2.iloc[0]:.1f} 吨 "
              f"（美国为中国 {usa_co2.iloc[0]/cn_co2.iloc[0]:.1f} 倍）")
    urban_gap = df[(df["year"] == LATEST) & (df["country_id"] == "CHN")]["urban"].iloc[0] - \
                df[df["year"] == LATEST]["urban"].median()
    print(f"5. {LATEST} 年中国城市化率高于全球中位数 {urban_gap:+.1f} 个百分点")

    chart_china(df)
    chart_income_life(df)
    chart_compare(df)
    print(f"\n图表已输出 -> {CHARTS}/")


if __name__ == "__main__":
    main()
