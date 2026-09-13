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
