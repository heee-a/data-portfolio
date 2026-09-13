"""文本挖掘：GitHub 头部仓库中 87 个中文描述项目的分词分析。

流程：筛中文描述 -> jieba 分词（含自定义词条）-> 停用词过滤 ->
词频/二连词统计 -> 图表。数据复用项目二的 repos.csv。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import jieba
import matplotlib.pyplot as plt
import pandas as pd

from datap.plotstyle import save_chart, setup_style

ROOT = Path(__file__).parent
CHARTS = ROOT / "charts"

STOPWORDS = set("""的 了 在 是 我 你 他 她 它 我们 你们 他们 和 与 及 或 等 对 从 被 把 让
一个 这个 那个 一些 一种 一款 基于 使用 可以 支持 提供 实现 用于 通过 以及 包括 进行 还有
not the for and with your from this that using build how to of on in is a an app""".split())
CUSTOM_WORDS = ["大模型", "人工智能", "机器学习", "深度学习", "计算机视觉", "自然语言处理",
                "面试", "中文", "开源项目", "监控系统", "前后端", "全栈", "笔记", "教程",
                "二次元", "本地部署", "知识库", "低代码"]


def has_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in str(text))


def tokenize(texts: list[str]) -> list[str]:
    for w in CUSTOM_WORDS:
        jieba.add_word(w)
    tokens = []
    for t in texts:
        for tok in jieba.cut(str(t)):
            tok = tok.strip().lower()
            if len(tok) < 2 or tok in STOPWORDS or tok.isdigit() or not any(
                    "\u4e00" <= ch <= "\u9fff" for ch in tok):
                continue
            tokens.append(tok)
    return tokens


def bigrams(tokens: list[str]) -> list[str]:
    return [f"{a}{b}" for a, b in zip(tokens, tokens[1:])]


def chart_freq(freq: pd.Series, title: str, path: Path, color: str) -> Path:
    setup_style()
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(freq.index[::-1], freq.values[::-1], color=color, alpha=0.9)
    for i, v in enumerate(freq.values[::-1]):
        ax.text(v + 0.15, i, str(v), va="center", fontsize=9)
    ax.set_xlabel("出现次数")
    ax.set_title(title)
    return save_chart(fig, path)


def main() -> None:
    df = pd.read_csv(ROOT.parent / "02_github_top" / "data" / "repos.csv")
    cn = df[df["description"].apply(has_cjk)].copy()
    cn["created_year"] = pd.to_datetime(cn["created_at"]).dt.year
    print(f"头部仓库中含中文描述的项目: {len(cn)} 个")

    tokens = tokenize(cn["description"].tolist())
    words = pd.Series(tokens).value_counts()
    bigr = pd.Series(bigrams(tokens)).value_counts()
    print(f"分词后共 {len(tokens):,} 个词，去重 {words.shape[0]} 个")

    print("\n=== 高频词 Top15 ===")
    print(words.head(15).to_string())
    print("\n=== 高频二连词 Top10 ===")
    print(bigr.head(10).to_string())
    print("\n=== 中文仓库语言分布 Top5 ===")
    print(cn["language"].value_counts().head(5).to_string())
    print(f"\n中文项目诞生的年份中位数: {cn['created_year'].median():.0f} "
          f"（全部仓库中位数 {pd.to_datetime(df['created_at']).dt.year.median():.0f}）")

    chart_freq(words.head(20), "中文项目描述高频词 Top20", CHARTS / "word_freq.png", "#4C72B0")
    chart_freq(bigr.head(15), "高频二连词 Top15", CHARTS / "bigram.png", "#55A868")

    lang = cn["language"].fillna("其他").value_counts().head(6)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(lang.index, lang.values, color="#DD8452", alpha=0.9)
    ax.set_title(f"含中文描述的头部仓库语言分布（n={len(cn)}）")
    save_chart(fig, CHARTS / "cn_repos_language.png")
    print(f"\n图表已输出 -> {CHARTS}/")

    words.head(30).to_csv(ROOT / "data" / "word_freq.csv", encoding="utf-8-sig")


if __name__ == "__main__":
    main()
