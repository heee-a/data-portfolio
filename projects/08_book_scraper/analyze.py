"""图书数据分析：价格分布、评分结构、价格-评分关系。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import matplotlib.pyplot as plt
import pandas as pd

from datap.plotstyle import save_chart, setup_style

ROOT = Path(__file__).resolve().parent


def main() -> None:
    setup_style()
    df = pd.read_csv(ROOT / "data" / "books_raw.csv")
    df["price_gbp"] = df["price_gbp"].round(2)

    print(f"数据: {len(df)} 本图书")
    print(f"价格: 均值 £{df['price_gbp'].mean():.2f}，中位数 £{df['price_gbp'].median():.2f}，"
          f"范围 £{df['price_gbp'].min():.2f} ~ £{df['price_gbp'].max():.2f}")
    rating_share = df["rating"].value_counts(normalize=True).sort_index() * 100
    print("评分分布(%):", {f"{k}星": round(v, 1) for k, v in rating_share.items()})
    by_rating = df.groupby("rating")["price_gbp"].mean().round(2)
    print("各评分均价:", by_rating.to_dict())

    # 图 1：价格分布
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.hist(df["price_gbp"], bins=36, color="#4C72B0", alpha=0.9)
    ax.axvline(df["price_gbp"].mean(), color="#C44E52", ls="--",
               label=f"均值 £{df['price_gbp'].mean():.2f}")
    ax.set_xlabel("价格 £")
    ax.set_ylabel("图书数")
    ax.set_title("1000 本图书的价格分布：均匀偏平，而非长尾")
    ax.legend()
    save_chart(fig, ROOT / "charts" / "price_hist.png")

    # 图 2：评分分布 + 各评分均价
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    counts = df["rating"].value_counts().sort_index()
    ax1.bar([f"{k}星" for k in counts.index], counts.values, color="#DD8452", alpha=0.9)
    ax1.set_title("评分分布：1 星与 5 星最多（沙盒数据刻意均匀）")
    ax2.bar([f"{k}星" for k in by_rating.index], by_rating.values, color="#55A868",
            alpha=0.9)
    ax2.set_title("各评分组均价：评分与价格无关联")
    ax2.set_ylabel("均价 £")
    save_chart(fig, ROOT / "charts" / "rating_structure.png")

    print("\n=== 结论（供 README 引用）===")
    print(f"1. 全部 {len(df)} 本均有货: {df['in_stock'].mean()*100:.0f}%")
    print(f"2. 价格近似均匀分布 £10~50（沙盒数据特征），均值 £{df['price_gbp'].mean():.2f}")
    print(f"3. 评分与价格零相关（Pearson "
          f"{df['rating'].corr(df['price_gbp']):.2f}）——分组均价几乎持平")


if __name__ == "__main__":
    main()
