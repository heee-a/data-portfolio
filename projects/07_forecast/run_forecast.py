"""时序预测：月均温的 Holt-Winters 季节模型 vs 季节朴素基线。

严谨点（面试可讲）：
- 时间序划分：2019-2023 训练，2024 整年做保留回测（不 Peek）；
- 与朴素基线（去年同月值）对比——季节性强的数据，模型必须先赢过它才有意义；
- 评估：MAE 与 MAPE；最后全量重拟合外推 2025 年 12 个月。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from datap.plotstyle import save_chart, setup_style

ROOT = Path(__file__).parent
CHARTS = ROOT / "charts"
CITIES = ["北京", "上海", "广州"]
TRAIN_END = 2023


def load_monthly() -> pd.DataFrame:
    daily = pd.read_csv(Path(__file__).resolve().parents[1] / "01_weather_cities"
                        / "data" / "weather_daily.csv", parse_dates=["date"])
    daily = daily[daily["city"].isin(CITIES)]
    m = (daily.groupby(["city", pd.Grouper(key="date", freq="MS")])["tmean"]
         .mean().reset_index().rename(columns={"date": "month", "tmean": "temp"}))
    return m


def seasonal_naive(train: pd.Series, n_test: int) -> np.ndarray:
    """基线：用训练集最后一个完整周期的同位置值（去年同月）。"""
    last_cycle = train.iloc[-12:].values
    reps = int(np.ceil(n_test / 12))
    return np.tile(last_cycle, reps)[:n_test]


def holt_winters(train: pd.Series, horizon: int) -> np.ndarray:
    model = ExponentialSmoothing(
        train.values, trend="add", seasonal="add", seasonal_periods=12,
        initialization_method="estimated")
    fit = model.fit(optimized=True)
    return fit.forecast(horizon)


def metrics(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[float, float]:
    mae = np.abs(y_true - y_pred).mean()
    mape = (np.abs(y_true - y_pred) / np.abs(y_true)).mean() * 100
    return mae, mape


def main() -> None:
    setup_style()
    monthly = load_monthly()
    results = []

    for city in CITIES:
        s = monthly[monthly["city"] == city].sort_values("month").set_index("month")["temp"]
        train = s[s.index.year <= TRAIN_END]
        test = s[s.index.year > TRAIN_END]

        preds = {"季节朴素基线": seasonal_naive(train, len(test)),
                 "Holt-Winters": holt_winters(train, len(test))}
        print(f"\n=== {city}（训练 {train.index.year.min()}-{TRAIN_END}，"
              f"回测 {test.index.year.min()}-{test.index.year.max()}）===")
        city_scores = {}
        for name, pred in preds.items():
            mae, mape = metrics(test.values, pred)
            city_scores[name] = (mae, mape)
            results.append({"city": city, "model": name,
                            "mae": round(mae, 2), "mape": round(mape, 1)})
            print(f"  {name:<8s} MAE={mae:.2f}℃  MAPE={mape:.1f}%")

        # 落后基线时如实报告
        if city_scores["Holt-Winters"][0] > city_scores["季节朴素基线"][0]:
            print("  -> Holt-Winters 未能击败朴素基线（如实报告）")
        else:
            print("  -> Holt-Winters 击败朴素基线")

    score_df = pd.DataFrame(results)
    score_df.to_csv(ROOT / "data" / "backtest_scores.csv", index=False,
                    encoding="utf-8-sig")

    # 全量重拟合并外推 2025
    fig, axes = plt.subplots(len(CITIES), 1, figsize=(10, 4 * len(CITIES)))
    forecasts_2025 = {}
    for ax, city in zip(axes, CITIES):
        s = monthly[monthly["city"] == city].sort_values("month").set_index("month")["temp"]
        hw = holt_winters(s, 12)
        forecasts_2025[city] = [round(v, 1) for v in hw]
        future = pd.date_range("2025-01-01", periods=12, freq="MS")
        ax.plot(s.index, s.values, label="实际", color="#4C72B0")
        ax.plot(future, hw, "--", marker=".", label="Holt-Winters 2025 预测",
                color="#C44E52")
        ax.axvline(s.index.max(), color="gray", ls=":", lw=1)
        ax.set_title(f"{city}：月均温与 2025 年外推")
        ax.set_ylabel("℃")
        ax.legend(fontsize=8)
    save_chart(fig, CHARTS / "forecast_2025.png")

    print("\n=== 2025 年预测（℃，Holt-Winters 全量重拟合）===")
    print(pd.DataFrame(forecasts_2025, index=[f"2025-{m:02d}" for m in range(1, 13)]))
    print("\n=== 回测汇总 ===")
    print(score_df.to_string(index=False))


if __name__ == "__main__":
    main()
