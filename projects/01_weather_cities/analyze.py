"""分析城市气象数据：温度对比、降水集中度、气候舒适度、升温趋势。

用法: python analyze.py
产出: charts/*.png + data/city_summary.csv（城市汇总表，供 README 引用）
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from datap.plotstyle import save_chart, setup_style

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "weather_daily.csv"
CHARTS = ROOT / "charts"

REPRESENT = ["哈尔滨", "北京", "上海", "广州", "成都", "昆明"]  # 曲线图代表城市


def load() -> pd.DataFrame:
    df = pd.read_csv(DATA, parse_dates=["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    return df


def city_summary(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("city")
    out = pd.DataFrame({
        "年均温℃": g["tmean"].mean().round(1),
        "最冷月均温℃": df.groupby(["city", "month"])["tmean"].mean()
                       .groupby("city").min().round(1),
        "最热月均温℃": df.groupby(["city", "month"])["tmean"].mean()
                       .groupby("city").max().round(1),
        "年降水mm": g["precip"].sum().div(6).round(0),          # 6 年均值
        "夏季降水占比%": df.assign(
            is_summer=df["month"].isin([6, 7, 8]))
            .groupby("city").apply(
                lambda x: x.loc[x["is_summer"], "precip"].sum()
                / x["precip"].sum() * 100, include_groups=False)
            .round(1),
        "年较差℃": (df.groupby(["city", "month"])["tmean"].mean()
                     .groupby("city").pipe(lambda s: s.max() - s.min())).round(1),
        "升温速率℃/年": g.apply(
            lambda x: pd.Series({"s": _slope(x)}), include_groups=False)["s"].round(3),
    })
    return out.sort_values("年均温℃", ascending=False)


def _slope(x: pd.DataFrame) -> float:
    """年均温对年份的线性斜率（℃/年）。"""
    yearly = x.groupby("year")["tmean"].mean()
    if yearly.notna().sum() < 3:
        return float("nan")
    return float(np.polyfit(yearly.index, yearly.values, 1)[0])


def chart_monthly(df: pd.DataFrame) -> Path:
    setup_style()
    fig, ax = plt.subplots(figsize=(10, 5))
    monthly = (df[df["city"].isin(REPRESENT)]
               .groupby(["city", "month"])["tmean"].mean().reset_index())
    for city in REPRESENT:
        sub = monthly[monthly["city"] == city]
        ax.plot(sub["month"], sub["tmean"], marker="o", ms=3.5, label=city)
    ax.set_xticks(range(1, 13), [f"{m}月" for m in range(1, 13)])
    ax.set_ylabel("月均温 ℃")
    ax.set_title("六城月均温曲线（2019-2024 均值）——南北冬差可近 40℃，夏差不足 10℃")
    ax.legend(ncols=3)
    return save_chart(fig, CHARTS / "monthly_temp.png")


def chart_precip(summary: pd.DataFrame) -> Path:
    setup_style()
    s = summary.sort_values("年降水mm", ascending=False)
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(s.index, s["年降水mm"], color="#4C72B0", alpha=0.9)
    for b, v in zip(bars, s["夏季降水占比%"]):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 25,
                f"{v:.0f}%", ha="center", fontsize=8, color="#555555")
    ax.set_ylabel("年均降水 mm（柱上数字=夏季占比）")
    ax.set_title("年均降水量对比：季风城市降水高度集中于夏季")
    ax.tick_params(axis="x", rotation=45)
    return save_chart(fig, CHARTS / "annual_precip.png")


def chart_range_vs_lat(df: pd.DataFrame) -> Path:
    setup_style()
    lat = {"哈尔滨": 45.8, "长春": 43.9, "乌鲁木齐": 43.8, "北京": 39.9, "兰州": 36.1,
           "郑州": 34.8, "西安": 34.3, "南京": 32.1, "上海": 31.2, "武汉": 30.6,
           "成都": 30.6, "重庆": 29.6, "杭州": 30.3, "拉萨": 29.7, "昆明": 25.0,
           "广州": 23.1, "深圳": 22.5, "三亚": 18.3}
    monthly = df.groupby(["city", "month"])["tmean"].mean()
    rng = (monthly.groupby("city").max() - monthly.groupby("city").min())
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.scatter([lat[c] for c in rng.index], rng.values, s=60, color="#C44E52", alpha=0.85)
    for c in rng.index:
        ax.annotate(c, (lat[c], rng[c]), fontsize=8,
                    xytext=(3, 3), textcoords="offset points")
    import numpy as np
    xs, ys = np.array([lat[c] for c in rng.index]), rng.values
    k, b = np.polyfit(xs, ys, 1)
    xx = np.linspace(xs.min(), xs.max(), 50)
    ax.plot(xx, k * xx + b, "--", color="gray", lw=1,
            label=f"线性拟合: 纬度+1° ≈ 年较差 +{k:.1f}℃")
    ax.set_xlabel("纬度 °N")
    ax.set_ylabel("温度年较差 ℃（最热月-最冷月）")
    ax.set_title("纬度越高，气候越「极端」：温度年较差与纬度强相关")
    ax.legend()
    return save_chart(fig, CHARTS / "range_vs_lat.png")


def chart_warming(summary: pd.DataFrame) -> Path:
    setup_style()
    s = summary.sort_values("升温速率℃/年", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = ["#C44E52" if v > 0 else "#4C72B0" for v in s["升温速率℃/年"]]
    ax.barh(s.index, s["升温速率℃/年"], color=colors, alpha=0.9)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_xlabel("2019-2024 年均温线性趋势 ℃/年（红=升温）")
    ax.set_title("六年间的温度变化趋势（注意：6 年太短，不代表气候结论）")
    return save_chart(fig, CHARTS / "warming_trend.png")


def main() -> None:
    df = load()
    print(f"数据: {len(df):,} 行 × {df['city'].nunique()} 城市, "
          f"{df['date'].min():%Y-%m-%d} ~ {df['date'].max():%Y-%m-%d}")

    summary = city_summary(df)
    summary.to_csv(ROOT / "data" / "city_summary.csv", encoding="utf-8-sig")
    print("\n=== 城市汇总（按年均温排序，前 8）===")
    print(summary.head(8).to_string())

    chart_monthly(df)
    chart_precip(summary)
    chart_range_vs_lat(df)
    chart_warming(summary)
    print(f"\n图表已输出 -> {CHARTS}/")

    print("\n=== 关键发现（供 README 引用）===")
    top_hot = summary["年均温℃"].idxmax()
    top_cold = summary["年均温℃"].idxmin()
    rain_max = summary["年降水mm"].idxmax()
    rain_min = summary["年降水mm"].idxmin()
    comfy = summary["年较差℃"].idxmin()
    summer = summary["夏季降水占比%"].idxmax()
    warm_fast = summary["升温速率℃/年"].idxmax()
    print(f"1. 年均温最高 {top_hot} {summary.loc[top_hot,'年均温℃']}℃ / 最低 {top_cold} "
          f"{summary.loc[top_cold,'年均温℃']}℃（差 {summary.loc[top_hot,'年均温℃']-summary.loc[top_cold,'年均温℃']:.1f}℃）")
    print(f"2. 最热月差: 全国 {summary['最热月均温℃'].min()}~{summary['最热月均温℃'].max()}℃ "
          f"而最冷月差 {summary['最冷月均温℃'].min()}~{summary['最冷月均温℃'].max()}℃ —— 冬差远大于夏差")
    print(f"3. 降水最多 {rain_max} {summary.loc[rain_max,'年降水mm']:.0f}mm / 最少 {rain_min} "
          f"{summary.loc[rain_min,'年降水mm']:.0f}mm"
          f"（{summary.loc[rain_max,'年降水mm']/summary.loc[rain_min,'年降水mm']:.1f}× 差距）; "
          f"{summer} 夏季降水占比最高({summary.loc[summer,'夏季降水占比%']}%)")
    print(f"4. 年较差最小（最四季如春）: {comfy} {summary.loc[comfy,'年较差℃']}℃")
    print(f"5. 样本期内升温最快: {warm_fast} {summary.loc[warm_fast,'升温速率℃/年']}℃/年（仅 6 年样本，勿过度解读）")


if __name__ == "__main__":
    main()
