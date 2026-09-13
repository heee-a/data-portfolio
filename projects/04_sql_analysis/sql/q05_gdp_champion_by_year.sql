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
