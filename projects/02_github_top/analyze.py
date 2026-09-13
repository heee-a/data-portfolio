"""分析 GitHub 头部仓库画像：语言构成、年代分布、star 幂律、topic 词频。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import matplotlib.pyplot as plt
import pandas as pd

from datap.plotstyle import save_chart, setup_style

ROOT = Path(__file__).parent
CHARTS = ROOT / "charts"


def load() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "data" / "repos.csv")
    df["created_year"] = pd.to_datetime(df["created_at"]).dt.year
    return df


def chart_language(df: pd.DataFrame) -> Path:
    setup_style()
    top = df["language"].fillna("其他/未标注").value_counts().head(10)
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(top.index[::-1], top.values[::-1], color="#4C72B0", alpha=0.9)
    for b, v in zip(bars, top.values[::-1]):
        ax.text(v + 1, b.get_y() + b.get_height() / 2, str(v), va="center", fontsize=9)
    ax.set_xlabel("仓库数")
    ax.set_title(f"头部开源仓库（stars>2万，共{len(df)}个）的语言构成")
    return save_chart(fig, CHARTS / "language.png")


def chart_year(df: pd.DataFrame) -> Path:
    setup_style()
    by_year = df.groupby("created_year").agg(
        仓库数=("full_name", "count"), 星标中位数=("stars", "median"))
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(by_year.index.astype(str), by_year["仓库数"], color="#4C72B0", alpha=0.9,
           label="仓库数")
    ax2 = ax.twinx()
    ax2.plot(by_year.index.astype(str), by_year["星标中位数"], color="#DD8452",
             marker="o", label="星标中位数")
    ax2.grid(False)
    ax2.set_ylabel("星标中位数")
    ax.set_ylabel("仓库数")
    ax.set_title("头部仓库诞生年代：2023 年（AI 潮）创峰值，2013-2018 为上一轮爆发期")
    ax.tick_params(axis="x", rotation=45)
    return save_chart(fig, CHARTS / "created_year.png")


def chart_star_distribution(df: pd.DataFrame) -> Path:
    setup_style()
    fig, ax = plt.subplots(figsize=(9, 5))
    stars = df["stars"].sort_values(ascending=False).reset_index(drop=True)
    ax.plot(range(1, len(stars) + 1), stars, color="#C44E52")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("排名（log）")
    ax.set_ylabel("星标数（log）")
    top1 = stars.iloc[0] / stars.median()
    ax.set_title(f"星标呈幂律分布：头部 1 名是中位数的 {top1:.0f} 倍")
    return save_chart(fig, CHARTS / "star_power_law.png")


def chart_topics(df: pd.DataFrame) -> Path:
    setup_style()
    topics = (
        df["topics"].dropna().str.split("|").explode().str.strip()
        .replace("", pd.NA).dropna()
    )
    top = topics.value_counts().head(15)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(top.index[::-1], top.values[::-1], color="#55A868", alpha=0.9)
    for i, v in enumerate(top.values[::-1]):
        ax.text(v + 0.5, i, str(v), va="center", fontsize=9)
    ax.set_xlabel("出现的头部仓库数")
    ax.set_title("头部仓库高频 topic Top15")
    return save_chart(fig, CHARTS / "topics.png")


def main() -> None:
    df = load()
    print(f"数据: {len(df)} 个仓库 (stars>=2万)")
    lang = df["language"].fillna("其他/未标注").value_counts()
    print(f"\nTop 语言: {dict(lang.head(5))}")

    print("\n=== 关键发现（供 README 引用）===")
    print(f"1. 语言第一 {lang.index[0]} 占 {lang.iloc[0]/len(df)*100:.0f}%；"
          f"前3语言合计 {lang.head(3).sum()/len(df)*100:.0f}%")
    yr = df.groupby("created_year").size()
    peak = yr.idxmax()
    print(f"2. 诞生峰值年 {peak}（{yr.max()} 个）；2013-2018 合计 "
          f"{yr.loc[2013:2018].sum() / len(df) * 100:.0f}%")
    print(f"3. 星标中位数 {df['stars'].median():.0f}，头部 {df.nlargest(1, 'stars').iloc[0]['full_name']} "
          f"{df['stars'].max():,}")
    no_license = 1 - df["has_license"].mean()
    print(f"4. 无 license 仓库占 {no_license*100:.0f}%")
    topics = df["topics"].dropna().str.split("|").explode().str.strip().replace("", pd.NA).dropna()
    print(f"5. 高频 topic: {dict(topics.value_counts().head(5))}")

    chart_language(df)
    chart_year(df)
    chart_star_distribution(df)
    chart_topics(df)
    print(f"\n图表已输出 -> {CHARTS}/")


if __name__ == "__main__":
    main()
