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
