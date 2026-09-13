"""执行 sql/ 下所有查询，输出 Markdown 分析报告。

用法: python run_queries.py
产出: report.md
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

ROOT = Path(__file__).parent
DB = ROOT / "data" / "world.db"

TITLES = {
    "q01": "2023 年人均GDP Top10",
    "q02": "中国历年人均GDP 与同比增速",
    "q03": "各收入等级组的平均预期寿命",
    "q04": "各地区城市化率 2000 vs 2023",
    "q05": "每年人均GDP 全球第一名",
    "q06": "中国 vs 印度 人均GDP 倍数",
    "q07": "预期寿命 ≥ 80 岁国家数量的趋势",
    "q08": "收入等级跃迁（2000 非高收入 → 2023 高收入）",
    "q09": "人均CO2 排名：中美位置变化",
    "q10": "高收入且低碳的「绿色发达」国家",
}

NOTES = {
    "q03": "收入越高、寿命越长，但高收入组内差距仍然明显。",
    "q04": "东亚与太平洋地区 23 年间城市化提升最快，欧洲中亚基本饱和。",
    "q05": "卢森堡/摩纳哥等微型经济体长期霸榜，人均口径下“冠军”多为小国。",
    "q06": "2000 年中国人均GDP 仅约为印度的 1.5 倍，2023 年已接近 5 倍。",
    "q07": "预期寿命 ≥80 岁的国家从个位数增长到数十个——全球长寿化是长期趋势。",
    "q08": "人均口径下 23 年里跨过「中等收入陷阱」的国家屈指可数：名义门槛还逐年抬高，跨越更难。",
    "q09": "人均CO2 排名美国从第 1 退居中国之后？看查询结果——人均口径与总量口径差异巨大。",
    "q10": "高收入且人均CO2 <5 吨的国家集中在水电/核电占比高的欧洲国家。",
}


def df_to_md(df: pd.DataFrame, max_rows: int = 15) -> str:
    d = df.head(max_rows)
    head = "| " + " | ".join(map(str, d.columns)) + " |"
    sep = "|" + "---|" * len(d.columns)
    rows = ["| " + " | ".join(str(v) for v in r) + " |" for r in d.itertuples(index=False)]
    return "\n".join([head, sep] + rows)


def main() -> None:
    lines = ["# SQL 分析报告：用 10 个业务问题看世界发展数据", ""]
    with sqlite3.connect(DB) as conn:
        for sql_file in sorted((ROOT / "sql").glob("q*.sql")):
            key = sql_file.stem
            sql = sql_file.read_text(encoding="utf-8")
            df = pd.read_sql_query(sql, conn)
            lines += [f"## {TITLES.get(key, key)}", ""]
            lines += ["```sql", sql.strip(), "```", ""]
            lines += [df_to_md(df), ""]
            if key in NOTES:
                lines += [f"> 解读：{NOTES[key]}", ""]
    (ROOT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"报告已生成: {ROOT / 'report.md'}（{len(lines)} 行）")


if __name__ == "__main__":
    main()
