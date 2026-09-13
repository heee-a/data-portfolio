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
