-- Q1 · 2023 年人均GDP Top10（JOIN 维表 + 排序）
SELECT c.country_name, c.region, ROUND(f.value, 0) AS gdp_per_capita_usd
FROM indicators f
JOIN countries c USING (country_id)
WHERE f.year = 2023 AND f.indicator_code = 'NY.GDP.PCAP.CD'
ORDER BY f.value DESC
LIMIT 10;
