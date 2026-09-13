"""采集全国主要城市 2019-2024 逐日气象数据（Open-Meteo Archive API，免费无 Key）。

用法: python collect.py
产出: data/weather_daily.csv（长表：city, date, tmax, tmean, tmin, precip）
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # 仓库根

import pandas as pd

from datap.fetching import Fetcher, ensure_dir

API = "https://archive-api.open-meteo.com/v1/archive"
START, END = "2019-01-01", "2024-12-31"

CITIES = {  # 覆盖东北/华北/华东/华南/西南/西北，兼顾沿海与内陆
    "北京": (39.90, 116.41), "上海": (31.23, 121.47), "广州": (23.13, 113.26),
    "深圳": (22.54, 114.06), "成都": (30.57, 104.07), "重庆": (29.56, 106.55),
    "武汉": (30.59, 114.31), "西安": (34.34, 108.94), "杭州": (30.27, 120.16),
    "南京": (32.06, 118.80), "哈尔滨": (45.80, 126.53), "长春": (43.88, 125.32),
    "乌鲁木齐": (43.83, 87.62), "拉萨": (29.65, 91.14), "昆明": (25.04, 102.72),
    "三亚": (18.25, 109.50), "兰州": (36.06, 103.83), "郑州": (34.75, 113.63),
}


def fetch_city(f: Fetcher, city: str, lat: float, lon: float) -> pd.DataFrame:
    data = f.get_json(API, params={
        "latitude": lat, "longitude": lon, "start_date": START, "end_date": END,
        "daily": "temperature_2m_max,temperature_2m_mean,temperature_2m_min,precipitation_sum",
        "timezone": "Asia/Shanghai",
    })
    daily = data["daily"]
    df = pd.DataFrame({
        "city": city,
        "date": pd.to_datetime(daily["time"]),
        "tmax": daily["temperature_2m_max"],
        "tmean": daily["temperature_2m_mean"],
        "tmin": daily["temperature_2m_min"],
        "precip": daily["precipitation_sum"],
    })
    return df


def main() -> None:
    root = ensure_dir(Path(__file__).parent / "data")
    f = Fetcher(cache_dir=root / ".cache", min_interval=3.0, max_retries=6)
    frames = []
    for i, (city, (lat, lon)) in enumerate(CITIES.items(), 1):
        df = fetch_city(f, city, lat, lon)
        frames.append(df)
        print(f"[{i:>2}/{len(CITIES)}] {city}: {len(df)} 天 "
              f"({df['date'].min():%Y-%m-%d} ~ {df['date'].max():%Y-%m-%d})")
    out = pd.concat(frames, ignore_index=True)
    out.to_csv(root / "weather_daily.csv", index=False, encoding="utf-8-sig")
    miss = out[["tmean", "precip"]].isna().mean().mul(100).round(2)
    print(f"\n合计 {len(out):,} 行 -> {root / 'weather_daily.csv'}")
    print(f"缺失率: tmean {miss['tmean']}% / precip {miss['precip']}%")


if __name__ == "__main__":
    main()
