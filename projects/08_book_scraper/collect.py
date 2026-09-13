"""HTML 爬虫：采集 books.toscrape.com 全站 1000 本图书（BeautifulSoup 解析）。

为什么选这个站：toscrape.com 是专为爬虫练习搭建的沙盒站点，
robots 与服务条款均允许抓取——教学演示的合规选择。

采集对象：目录页 50 页 × 每页 20 本（书名/价格/评分/库存/CSS 选择器实践）。
协议：1 秒限速 + 磁盘缓存 + 429 退避（复用共享 Fetcher）。
产出: data/books_raw.csv

运行: python collect.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from datap.fetching import Fetcher, ensure_dir

BASE = "https://books.toscrape.com/catalogue/page-{page}.html"
TOTAL_PAGES = 50

RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def parse_page(html: str) -> list[dict]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    out = []
    for art in soup.select("article.product_pod"):
        rating_class = next(
            (c for c in art.select_one("p.star-rating")["class"] if c != "star-rating"),
            "Zero")
        title = art.select_one("h3 a")["title"]
        price = art.select_one("p.price_color").get_text(strip=True)
        availability = art.select_one("p.instock.availability").get_text(strip=True)
        out.append({
            "title": title,
            "price_gbp": float(price.replace("£", "").replace("Â", "")),
            "rating": RATING_MAP.get(rating_class, 0),
            "in_stock": "In stock" in availability,
        })
    return out


def main() -> None:
    root = ensure_dir(Path(__file__).parent / "data")
    f = Fetcher(cache_dir=root / ".cache", min_interval=1.0)

    rows = []
    for page in range(1, TOTAL_PAGES + 1):
        html = f.sess.get(BASE.format(page=page), timeout=30).text
        page_rows = parse_page(html)
        rows.extend(page_rows)
        if page % 10 == 0 or page == 1:
            print(f"page {page:>2}: 累计 {len(rows)} 本")

    df = pd.DataFrame(rows).drop_duplicates(subset=["title"])
    df.to_csv(root / "books_raw.csv", index=False, encoding="utf-8-sig")
    print(f"\n合计 {len(df)} 本图书 -> {root / 'books_raw.csv'}")
    print(df["rating"].value_counts().sort_index().to_string())


if __name__ == "__main__":
    main()
