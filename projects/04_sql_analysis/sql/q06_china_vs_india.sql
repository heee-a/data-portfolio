-- Q6 · 中国 vs 印度 人均GDP 倍数时间序列（条件聚合自比较）
SELECT f.year,
       ROUND(MAX(CASE WHEN f.country_id = 'CHN' THEN f.value END)
           / MAX(CASE WHEN f.country_id = 'IND' THEN f.value END), 2) AS china_vs_india
FROM indicators f
WHERE f.indicator_code = 'NY.GDP.PCAP.CD'
      AND f.country_id IN ('CHN', 'IND') AND f.year >= 2000
GROUP BY f.year
ORDER BY f.year;
