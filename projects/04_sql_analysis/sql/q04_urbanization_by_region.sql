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
