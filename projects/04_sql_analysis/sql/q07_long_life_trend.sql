-- Q7 · 预期寿命 ≥ 80 岁的国家数量按年份趋势（长期改善的量化）
SELECT f.year,
       COUNT(*) AS countries_with_le80
FROM indicators f
WHERE f.indicator_code = 'SP.DYN.LE00.IN' AND f.value >= 80
GROUP BY f.year
ORDER BY f.year;
