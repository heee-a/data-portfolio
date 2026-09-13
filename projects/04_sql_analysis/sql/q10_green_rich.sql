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
