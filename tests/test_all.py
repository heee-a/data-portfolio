"""作品集测试：采集器缓存逻辑（离线）+ 已提交数据的质量回归。pytest -q"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from datap.fetching import Fetcher

REPO = Path(__file__).resolve().parents[1]


# ---------------- fetching ----------------
def test_cache_hit_avoids_network(tmp_path, monkeypatch):
    """缓存命中时不应发出任何网络请求（把 Session.get 改成必炸来验证）。"""
    f = Fetcher(cache_dir=tmp_path)
    url = "https://example.com/api"
    cache = f._cache_path(url)
    cache.write_text('{"ok": 1}', encoding="utf-8")

    def boom(*a, **k):
        raise AssertionError("缓存命中不应发起网络请求")

    monkeypatch.setattr(f.sess, "get", boom)
    assert f.get_json(url) == {"ok": 1}


def test_url_params_are_stable_for_cache(tmp_path):
    """缓存路径对 URL 确定性：同 URL 同路径，不同 URL 不同路径。"""
    f = Fetcher(cache_dir=tmp_path)
    assert f._cache_path("https://x/api?a=1&b=2") == f._cache_path("https://x/api?a=1&b=2")
    assert f._cache_path("https://x/api?a=1&b=2") != f._cache_path("https://x/api?a=2&b=2")


def test_throttle_enforces_interval(tmp_path):
    import time

    f = Fetcher(cache_dir=tmp_path, min_interval=0.2)
    t0 = time.time()
    f._throttle()
    f._throttle()
    assert time.time() - t0 >= 0.19


# ---------------- 已提交数据的质量回归 ----------------
def test_weather_data_quality():
    df = pd.read_csv(REPO / "projects/01_weather_cities/data/weather_daily.csv",
                     parse_dates=["date"])
    assert len(df) == 39456
    assert df["city"].nunique() == 18
    assert df["date"].min().year == 2019 and df["date"].max().year == 2024
    assert df[["tmean", "tmax", "tmin", "precip"]].isna().sum().sum() == 0
    assert (df["tmax"] >= df["tmin"]).all()          # 物理一致性
    assert df["tmean"].between(-45, 45).all()        # 合理范围


def test_city_summary_consistent():
    s = pd.read_csv(REPO / "projects/01_weather_cities/data/city_summary.csv",
                    index_col=0)
    # 年较差由未取整的月度均值之差四舍五入而来，允许 0.15℃ 舍入误差
    diff = (s["年较差℃"] - (s["最热月均温℃"] - s["最冷月均温℃"])).abs()
    assert (diff <= 0.15).all()


def test_github_repos_quality():
    df = pd.read_csv(REPO / "projects/02_github_top/data/repos.csv")
    assert len(df) == 1000
    assert df["full_name"].is_unique
    assert (df["stars"] >= 30000).all()
    assert df["stars"].is_monotonic_decreasing       # 按星标降序
    assert df["created_at"].str.len().eq(10).all()


def test_world_indicators_quality():
    df = pd.read_csv(REPO / "projects/03_world_indicators/data/indicators_long.csv")
    assert set(df["indicator_name"]) == {"人均GDP美元", "预期寿命", "人均CO2吨", "城市化率%"}
    assert df["year"].between(2000, 2023).all()
    assert df["country_id"].nunique() >= 200
    assert (df["value"] >= 0).all()                  # 四个指标都非负


# ---------------- 新增项目（SQL / 预测 / 文本） ----------------
def test_sqlite_db_quality():
    import sqlite3

    db = REPO / "projects/04_sql_analysis/data/world.db"
    with sqlite3.connect(db) as conn:
        facts = pd.read_sql_query("SELECT * FROM indicators", conn)
        dims = pd.read_sql_query("SELECT * FROM countries", conn)
    assert len(facts) == 20330
    assert len(dims) == 217
    assert set(facts["indicator_code"]) == {
        "NY.GDP.PCAP.CD", "SP.DYN.LE00.IN", "EN.GHG.CO2.PC.CE.AR5", "SP.URB.TOTL.IN.ZS"}


def test_sql_report_covers_all_questions():
    text = (REPO / "projects/04_sql_analysis/report.md").read_text(encoding="utf-8")
    for i in range(1, 11):
        assert f"q{i:02d}" in text.lower() or f"Q{i:02d}" in text


def test_backtest_scores():
    s = pd.read_csv(REPO / "projects/07_forecast/data/backtest_scores.csv")
    assert len(s) == 6 and set(s["model"]) == {"季节朴素基线", "Holt-Winters"}
    assert (s["mae"] < 5).all()                      # 月均温预测误差应在几度内


def test_word_freq_output():
    w = pd.read_csv(REPO / "projects/06_text_mining/data/word_freq.csv",
                    index_col=0).iloc[:, 0]
    assert len(w) == 30
    assert (w.diff().dropna() <= 0).all()            # 按词频降序
