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
