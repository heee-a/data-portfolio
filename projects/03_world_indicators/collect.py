"""采集世界发展指标（World Bank API v2，公开免费）：人均GDP/预期寿命/CO2/城市化。

用法: python collect.py
产出: data/indicators_long.csv（长表） + data/countries.csv（国家元数据，用于剔除聚合区）
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from datap.fetching import Fetcher, ensure_dir

API = "https://api.worldbank.org/v2"
INDICATORS = {  # 指标代码 -> 中文含义（CO2 用 2024 后的新代码，旧码 EN.ATM.CO2E.PC 已归档）
    "NY.GDP.PCAP.CD": "人均GDP美元",
    "SP.DYN.LE00.IN": "预期寿命",
    "EN.GHG.CO2.PC.CE.AR5": "人均CO2吨",
    "SP.URB.TOTL.IN.ZS": "城市化率%",
}


def main() -> None:
    root = ensure_dir(Path(__file__).parent / "data")
    f = Fetcher(cache_dir=root / ".cache", min_interval=1.0)

    # 国家元数据：剔除 Aggregates（欧盟、世界等聚合区不是国家）
    meta = f.get_json(f"{API}/country", params={"format": "json", "per_page": 400})
    countries = pd.DataFrame(meta[1])
    countries["region_name"] = countries["region"].apply(
        lambda d: d.get("value") if isinstance(d, dict) else None)
    countries["income_name"] = countries["incomeLevel"].apply(
        lambda d: d.get("value") if isinstance(d, dict) else None)
    countries = countries[countries["region_name"] != "Aggregates"]
    valid_ids = set(countries["id"])
    countries[["id", "name", "region_name", "income_name"]].to_csv(
        root / "countries.csv", index=False, encoding="utf-8-sig")
    print(f"国家/地区: {len(valid_ids)}（已剔除聚合区）")

    frames = []
    for code, name in INDICATORS.items():
        data = f.get_json(f"{API}/country/all/indicator/{code}", params={
            "format": "json", "per_page": 20000, "date": "2000:2023"})
        rows = data[1] or []
        frames.append(pd.DataFrame([{
            "country_id": r["countryiso3code"],
            "country": r["country"]["value"],
            "year": int(r["date"]),
            "indicator": code,
            "indicator_name": name,
            "value": r["value"],
        } for r in rows if r["value"] is not None and r["countryiso3code"] in valid_ids]))
        print(f"{name}: {len(frames[-1]):,} 行")

    out = pd.concat(frames, ignore_index=True)
    out.to_csv(root / "indicators_long.csv", index=False, encoding="utf-8-sig")
    print(f"\n合计 {len(out):,} 行 -> {root / 'indicators_long.csv'}")


if __name__ == "__main__":
    main()
