"""把世界发展指标导入 SQLite：一张事实表 + 一张维表（星型雏形）。

用法: python build_db.py
产出: data/world.db
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

ROOT = Path(__file__).parent
DB = ROOT / "data" / "world.db"
IND_CODE = {"人均GDP美元": "NY.GDP.PCAP.CD", "预期寿命": "SP.DYN.LE00.IN",
            "人均CO2吨": "EN.GHG.CO2.PC.CE.AR5", "城市化率%": "SP.URB.TOTL.IN.ZS"}


def main() -> None:
    DB.parent.mkdir(parents=True, exist_ok=True)
    if DB.exists():
        DB.unlink()
    long_df = pd.read_csv(ROOT.parent / "03_world_indicators" / "data" / "indicators_long.csv")
    countries = pd.read_csv(ROOT.parent / "03_world_indicators" / "data" / "countries.csv")

    facts = long_df.copy()
    facts["indicator_code"] = facts["indicator_name"].map(IND_CODE)
    facts = facts[["country_id", "year", "indicator_code", "value"]]

    dims = countries.rename(columns={"id": "country_id", "name": "country_name",
                                     "region_name": "region", "income_name": "income_level"})

    with sqlite3.connect(DB) as conn:
        dims.to_sql("countries", conn, index=False)
        facts.to_sql("indicators", conn, index=False)
        conn.execute("CREATE INDEX idx_ind ON indicators(country_id, year, indicator_code)")
        n1 = conn.execute("SELECT COUNT(*) FROM indicators").fetchone()[0]
        n2 = conn.execute("SELECT COUNT(*) FROM countries").fetchone()[0]
    print(f"world.db: indicators {n1:,} 行 / countries {n2} 行")


if __name__ == "__main__":
    main()
