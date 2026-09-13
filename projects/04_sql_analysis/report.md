# SQL 分析报告：用 10 个业务问题看世界发展数据

## q01_gdp_top10_2023

```sql
-- Q1 · 2023 年人均GDP Top10（JOIN 维表 + 排序）
SELECT c.country_name, c.region, ROUND(f.value, 0) AS gdp_per_capita_usd
FROM indicators f
JOIN countries c USING (country_id)
WHERE f.year = 2023 AND f.indicator_code = 'NY.GDP.PCAP.CD'
ORDER BY f.value DESC
LIMIT 10;
```

| country_name | region | gdp_per_capita_usd |
|---|---|---|
| Monaco | Europe & Central Asia | 256800.0 |
| Liechtenstein | Europe & Central Asia | 206781.0 |
| Luxembourg | Europe & Central Asia | 133231.0 |
| Bermuda | North America | 132962.0 |
| Ireland | Europe & Central Asia | 106819.0 |
| Switzerland | Europe & Central Asia | 104450.0 |
| Cayman Islands | Latin America & Caribbean  | 100065.0 |
| Norway | Europe & Central Asia | 90984.0 |
| Isle of Man | Europe & Central Asia | 90015.0 |
| Singapore | East Asia & Pacific | 86383.0 |

## q02_china_gdp_yoy

```sql
-- Q2 · 中国历年人均GDP 及同比增速（LAG 窗口函数）
WITH cn AS (
    SELECT year, value
    FROM indicators
    WHERE country_id = 'CHN' AND indicator_code = 'NY.GDP.PCAP.CD'
)
SELECT year,
       ROUND(value, 0) AS gdp_usd,
       ROUND((value * 1.0 / LAG(value) OVER (ORDER BY year) - 1) * 100, 1) AS yoy_pct
FROM cn
ORDER BY year;
```

| year | gdp_usd | yoy_pct |
|---|---|---|
| 2000 | 969.0 | nan |
| 2001 | 1065.0 | 9.9 |
| 2002 | 1164.0 | 9.2 |
| 2003 | 1307.0 | 12.3 |
| 2004 | 1531.0 | 17.1 |
| 2005 | 1778.0 | 16.1 |
| 2006 | 2129.0 | 19.8 |
| 2007 | 2735.0 | 28.4 |
| 2008 | 3523.0 | 28.8 |
| 2009 | 3898.0 | 10.6 |
| 2010 | 4629.0 | 18.8 |
| 2011 | 5704.0 | 23.2 |
| 2012 | 6405.0 | 12.3 |
| 2013 | 7147.0 | 11.6 |
| 2014 | 7781.0 | 8.9 |

## q03_life_by_income

```sql
-- Q3 · 2023 年各收入等级组的平均预期寿命与国家数（CASE + JOIN + HAVING）
SELECT c.income_level,
       COUNT(*) AS countries,
       ROUND(AVG(f.value), 1) AS avg_life_expectancy
FROM indicators f
JOIN countries c USING (country_id)
WHERE f.year = 2023 AND f.indicator_code = 'SP.DYN.LE00.IN'
GROUP BY c.income_level
HAVING COUNT(*) >= 5
ORDER BY avg_life_expectancy DESC;
```

| income_level | countries | avg_life_expectancy |
|---|---|---|
| High income | 86 | 79.8 |
| Upper middle income | 59 | 73.8 |
| Lower middle income | 47 | 67.9 |
| Low income | 25 | 64.2 |

## q04_urbanization_by_region

```sql
-- Q4 · 各地区城市化率 2000 vs 2023 对比（条件聚合透视）
SELECT c.region,
       ROUND(AVG(CASE WHEN f.year = 2000 THEN f.value END), 1) AS urban_2000,
       ROUND(AVG(CASE WHEN f.year = 2023 THEN f.value END), 1) AS urban_2023,
       ROUND(AVG(CASE WHEN f.year = 2023 THEN f.value END)
           - AVG(CASE WHEN f.year = 2000 THEN f.value END), 1) AS change_pp
FROM indicators f
JOIN countries c USING (country_id)
WHERE f.indicator_code = 'SP.URB.TOTL.IN.ZS' AND f.year IN (2000, 2023)
GROUP BY c.region
ORDER BY change_pp DESC;
```

| region | urban_2000 | urban_2023 | change_pp |
|---|---|---|---|
| South Asia | 25.3 | 39.5 | 14.2 |
| Sub-Saharan Africa  | 34.3 | 45.2 | 10.9 |
| East Asia & Pacific | 54.8 | 62.5 | 7.8 |
| Middle East, North Africa, Afghanistan & Pakistan | 68.6 | 75.5 | 6.9 |
| Europe & Central Asia | 63.7 | 68.1 | 4.4 |
| Latin America & Caribbean  | 65.2 | 69.5 | 4.3 |
| North America | 85.9 | 87.5 | 1.6 |

## q05_gdp_champion_by_year

```sql
-- Q5 · 每年人均GDP 全球第一名（窗口函数经典：ROW_NUMBER OVER PARTITION）
WITH ranked AS (
    SELECT f.year, c.country_name, f.value,
           ROW_NUMBER() OVER (PARTITION BY f.year ORDER BY f.value DESC) AS rn
    FROM indicators f
    JOIN countries c USING (country_id)
    WHERE f.indicator_code = 'NY.GDP.PCAP.CD' AND f.year >= 2000
)
SELECT year, country_name, ROUND(value, 0) AS gdp_per_capita_usd
FROM ranked
WHERE rn = 1
ORDER BY year;
```

| year | country_name | gdp_per_capita_usd |
|---|---|---|
| 2000 | Monaco | 81789.0 |
| 2001 | Monaco | 82403.0 |
| 2002 | Monaco | 90051.0 |
| 2003 | Monaco | 111110.0 |
| 2004 | Monaco | 125160.0 |
| 2005 | Monaco | 130539.0 |
| 2006 | Monaco | 143084.0 |
| 2007 | Monaco | 184558.0 |
| 2008 | Monaco | 204264.0 |
| 2009 | Monaco | 169150.0 |
| 2010 | Monaco | 161854.0 |
| 2011 | Monaco | 179364.0 |
| 2012 | Monaco | 165445.0 |
| 2013 | Monaco | 184941.0 |
| 2014 | Monaco | 195694.0 |

## q06_china_vs_india

```sql
-- Q6 · 中国 vs 印度 人均GDP 倍数时间序列（条件聚合自比较）
SELECT f.year,
       ROUND(MAX(CASE WHEN f.country_id = 'CHN' THEN f.value END)
           / MAX(CASE WHEN f.country_id = 'IND' THEN f.value END), 2) AS china_vs_india
FROM indicators f
WHERE f.indicator_code = 'NY.GDP.PCAP.CD'
      AND f.country_id IN ('CHN', 'IND') AND f.year >= 2000
GROUP BY f.year
ORDER BY f.year;
```

| year | china_vs_india |
|---|---|
| 2000 | 2.19 |
| 2001 | 2.37 |
| 2002 | 2.48 |
| 2003 | 2.4 |
| 2004 | 2.45 |
| 2005 | 2.5 |
| 2006 | 2.66 |
| 2007 | 2.68 |
| 2008 | 3.55 |
| 2009 | 3.56 |
| 2010 | 3.44 |
| 2011 | 3.95 |
| 2012 | 4.48 |
| 2013 | 4.99 |
| 2014 | 5.01 |

## q07_long_life_trend

```sql
-- Q7 · 预期寿命 ≥ 80 岁的国家数量按年份趋势（长期改善的量化）
SELECT f.year,
       COUNT(*) AS countries_with_le80
FROM indicators f
WHERE f.indicator_code = 'SP.DYN.LE00.IN' AND f.value >= 80
GROUP BY f.year
ORDER BY f.year;
```

| year | countries_with_le80 |
|---|---|
| 2000 | 7 |
| 2001 | 10 |
| 2002 | 10 |
| 2003 | 11 |
| 2004 | 16 |
| 2005 | 20 |
| 2006 | 23 |
| 2007 | 25 |
| 2008 | 28 |
| 2009 | 33 |
| 2010 | 34 |
| 2011 | 37 |
| 2012 | 41 |
| 2013 | 44 |
| 2014 | 45 |

## q08_income_upgrades

```sql
-- Q8 · 收入等级跃迁的国家：2000 年非高收入 -> 2023 年高收入
-- 口径：按世界银行当年名义门槛分层（2000：高收入≥9266；2023：高收入≥14005 美元）
WITH y2000 AS (
    SELECT country_id,
           CASE WHEN value >= 9266 THEN '高收入'
                WHEN value >= 2995 THEN '中高收入'
                WHEN value >= 755  THEN '中低收入'
                ELSE '低收入' END AS band
    FROM indicators
    WHERE year = 2000 AND indicator_code = 'NY.GDP.PCAP.CD'
),
y2023 AS (
    SELECT country_id,
           CASE WHEN value >= 14005 THEN '高收入'
                WHEN value >= 4516  THEN '中高收入'
                WHEN value >= 1146  THEN '中低收入'
                ELSE '低收入' END AS band
    FROM indicators
    WHERE year = 2023 AND indicator_code = 'NY.GDP.PCAP.CD'
)
SELECT y2000.band AS band_2000,
       y2023.band AS band_2023,
       COUNT(DISTINCT y2023.country_id) AS countries,
       GROUP_CONCAT(DISTINCT c.country_name) AS names
FROM y2000
JOIN y2023 USING (country_id)
JOIN countries c USING (country_id)
WHERE y2000.band != '高收入' AND y2023.band = '高收入'
GROUP BY y2000.band, y2023.band
ORDER BY countries DESC;
```

| band_2000 | band_2023 | countries | names |
|---|---|---|---|
| 中高收入 | 高收入 | 16 | Argentina,Chile,Costa Rica,Croatia,Czechia,Estonia,Hungary,Latvia,Lithuania,Palau,Panama,Poland,Seychelles,Slovak Republic,Trinidad and Tobago,Uruguay |
| 中低收入 | 高收入 | 3 | Bulgaria,Guyana,Romania |

## q09_co2_rank

```sql
-- Q9 · 人均CO2 Top10 国家的中国排名变化（2000 vs 2023，RANK 窗口）
WITH ranked AS (
    SELECT f.year, c.country_name, f.value,
           RANK() OVER (PARTITION BY f.year ORDER BY f.value DESC) AS rk
    FROM indicators f
    JOIN countries c USING (country_id)
    WHERE f.indicator_code = 'EN.GHG.CO2.PC.CE.AR5' AND f.year IN (2000, 2023)
)
SELECT year, country_name, ROUND(value, 2) AS co2_tons, rk
FROM ranked
WHERE country_name IN ('China', 'United States') OR rk <= 10
ORDER BY year, rk;
```

| year | country_name | co2_tons | rk |
|---|---|---|---|
| 2000 | Palau | 110.65 | 1 |
| 2000 | Qatar | 49.23 | 2 |
| 2000 | Kuwait | 28.66 | 3 |
| 2000 | Bahrain | 27.87 | 4 |
| 2000 | United Arab Emirates | 25.32 | 5 |
| 2000 | United States | 21.01 | 6 |
| 2000 | Luxembourg | 20.17 | 7 |
| 2000 | Brunei Darussalam | 18.61 | 8 |
| 2000 | Australia | 18.6 | 9 |
| 2000 | Canada | 17.7 | 10 |
| 2000 | China | 2.89 | 86 |
| 2023 | Palau | 78.86 | 1 |
| 2023 | Qatar | 48.64 | 2 |
| 2023 | Bahrain | 24.53 | 3 |
| 2023 | Kuwait | 22.7 | 4 |

## q10_green_rich

```sql
-- Q10 · 2023 年「高收入但人均CO2 低于 5 吨」的绿色发达国家（多条件业务筛选）
SELECT c.country_name, c.region,
       ROUND(g.value, 0) AS gdp_per_capita_usd,
       ROUND(e.value, 2) AS co2_tons_per_capita
FROM indicators g
JOIN indicators e ON e.country_id = g.country_id AND e.year = g.year
                     AND e.indicator_code = 'EN.GHG.CO2.PC.CE.AR5'
JOIN countries c USING (country_id)
WHERE g.year = 2023 AND g.indicator_code = 'NY.GDP.PCAP.CD'
  AND c.income_level = 'High income' AND e.value < 5
ORDER BY g.value DESC;
```

| country_name | region | gdp_per_capita_usd | co2_tons_per_capita |
|---|---|---|---|
| Bermuda | North America | 132962.0 | 3.99 |
| Switzerland | Europe & Central Asia | 104450.0 | 3.79 |
| Cayman Islands | Latin America & Caribbean  | 100065.0 | 4.92 |
| Faroe Islands | Europe & Central Asia | 72487.0 | 0.04 |
| Denmark | Europe & Central Asia | 68044.0 | 4.41 |
| Macao SAR, China | East Asia & Pacific | 67216.0 | 2.48 |
| Sweden | Europe & Central Asia | 54950.0 | 3.48 |
| Hong Kong SAR, China | East Asia & Pacific | 50525.0 | 4.53 |
| United Kingdom | Europe & Central Asia | 49920.0 | 4.45 |
| France | Europe & Central Asia | 44700.0 | 4.16 |
| Malta | Middle East, North Africa, Afghanistan & Pakistan | 40933.0 | 3.23 |
| Bahamas, The | Latin America & Caribbean  | 38232.0 | 3.53 |
| Puerto Rico (US) | Latin America & Caribbean  | 36981.0 | 4.57 |
| Turks and Caicos Islands | Latin America & Caribbean  | 35470.0 | 4.79 |
| Spain | Europe & Central Asia | 33493.0 | 4.57 |
