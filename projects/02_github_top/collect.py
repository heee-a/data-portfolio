"""采集 GitHub 头部开源仓库（Search API，stars>20000，分页拉满）。

用法: python collect.py
产出: data/repos.csv
说明: 未认证 Search API 限速 10 次/分钟，这里强制 7s 间隔 + 429 退避；
      结果缓存到 .cache，重跑不重复请求。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from datap.fetching import Fetcher, ensure_dir

API = "https://api.github.com/search/repositories"
MIN_STARS = 30000  # GitHub 搜索 API 最多返回 1000 条，取 3 万星以上保证可全量分页


def main() -> None:
    root = ensure_dir(Path(__file__).parent / "data")
    f = Fetcher(cache_dir=root / ".cache", min_interval=7.0, max_retries=5)

    rows, page = [], 1
    while True:
        try:
            data = f.get_json(API, params={
                "q": f"stars:>{MIN_STARS}",
                "sort": "stars", "order": "desc",
                "per_page": 100, "page": page,
            })
        except RuntimeError:
            if page > 1:  # GitHub 搜索最多返回前 1000 条，第 11 页报 422
                print(f"page {page} 失败（搜索 API 上限 1000 条），按已获取的头部数据停止")
                break
            raise
        items = data.get("items", [])
        print(f"page {page}: {len(items)} 个仓库 "
              f"(total_count={data.get('total_count')})")
        if not items:
            break
        for r in items:
            rows.append({
                "full_name": r["full_name"],
                "owner": r["owner"]["login"],
                "language": r["language"],
                "stars": r["stargazers_count"],
                "forks": r["forks_count"],
                "open_issues": r["open_issues_count"],
                "created_at": r["created_at"][:10],
                "pushed_at": r["pushed_at"][:10],
                "size_kb": r["size"],
                "topics": "|".join(r.get("topics") or []),
                "has_license": int(bool(r.get("license"))),
                "description": (r.get("description") or "")[:120],
            })
        if len(items) < 100:
            break
        page += 1

    df = pd.DataFrame(rows).drop_duplicates("full_name")
    df.to_csv(root / "repos.csv", index=False, encoding="utf-8-sig")
    print(f"\n合计 {len(df)} 个仓库 -> {root / 'repos.csv'}")


if __name__ == "__main__":
    main()
