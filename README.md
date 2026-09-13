# data-portfolio · 数据采集与分析作品集

面向数据分析岗位的实战作品集：三个完整的小项目，每个都走完
**采集 → 清洗 → 分析 → 可视化 → 结论** 全链路。所有数据、图表、结论均由
仓库内脚本从公开数据源真实采集生成，可一键复现。

## 项目一览

| 项目 | 数据源 | 采集量 | 分析亮点 |
|---|---|---|---|
| [01 全国主要城市气象分析](projects/01_weather_cities/) | Open-Meteo Archive API | 18 城 × 6 年逐日，39,456 行 | 南北冬差 37℃ vs 夏差 13℃；年较差与纬度线性关系；降水集中度 |
| [02 GitHub 头部仓库画像](projects/02_github_top/) | GitHub Search API | 1000 个 3 万星以上仓库 | Python 占 23%；诞生峰值 2023（AI 潮）；星标幂律分布 |
| [03 世界发展指标](projects/03_world_indicators/) | World Bank API v2 | 217 国 × 24 年 × 4 指标，20,330 行 | 中国人均GDP 13.4×；收入-寿命 Spearman 0.86 |

每个项目的目录里都有独立的 README（数据来源、清洗口径、结论、复现命令），
以及 `collect.py`（采集）与 `analyze.py`（分析出图）。

## 工程实践（面试可展开讲）

- **礼貌采集基座** [datap/fetching.py](datap/fetching.py)：
  - 磁盘缓存——同 URL 只请求一次，重跑分析零请求；
  - 限速 + 指数退避 + `Retry-After` 尊重——项目一中真实触发过 Open-Meteo
    每分钟限流（共享出口 IP），自动等待 61s 后恢复，全程无人值守；
  - 项目二踩到 GitHub 搜索 API「最多返回 1000 条」的硬上限（第 11 页 422），
    采集器按业务边界优雅终止并在 README 中如实记录；
- **数据质量**：每个项目 README 报告缺失率与分析口径；仓库附带数据质量
  回归测试（`tests/`），防止脏数据被当成结论；
- **诚实呈现**：6 年温度趋势明确标注"样本太短，勿过度解读"；GitHub 数据
  明确标注"头部幸存者画像"——面试时这是加分项。

## 快速开始

```bash
pip install -e .
# 任选一个项目
cd projects/01_weather_cities
python collect.py   # 首次真实采集（含限速等待，有缓存后秒级）
python analyze.py   # 出图表与结论
```

## 目录结构

```
data-portfolio/
├── datap/                  # 共享库：限速/重试/缓存采集器 + 图表样式
├── projects/
│   ├── 01_weather_cities/  # 天气：collect.py + analyze.py + README + data/ + charts/
│   ├── 02_github_top/
│   └── 03_world_indicators/
└── tests/                  # 数据质量回归测试 + 采集器缓存单测
```

## 数据与版权说明

三个数据源均为公开 API，允许程序化访问；本仓库以研究学习为目的采集，
遵守其服务条款与限速要求。采集日期：2026-09（数据快照随仓库提供，
重跑 `collect.py` 可刷新）。

## License

[MIT](LICENSE)
