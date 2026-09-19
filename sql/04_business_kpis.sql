USE supplypulse;

WITH demand AS (
    SELECT
        sku_id,
        AVG(units_sold) AS avg_daily_demand,
        STDDEV_POP(units_sold) AS demand_std
    FROM v_inventory_clean
    WHERE inventory_date > (SELECT MAX(inventory_date) FROM v_inventory_clean) - INTERVAL 28 DAY
    GROUP BY sku_id
),
latest AS (
    SELECT *
    FROM (
        SELECT i.*, ROW_NUMBER() OVER (PARTITION BY sku_id ORDER BY inventory_date DESC) AS rn
        FROM v_inventory_clean i
    ) x
    WHERE rn = 1
)
SELECT
    SUM(l.units_on_hand * l.unit_cost) AS inventory_value,
    COUNT(DISTINCT l.sku_id) AS sku_count,
    SUM(
        CASE
            WHEN l.units_on_hand < d.avg_daily_demand * l.lead_time_days
                + 1.6449 * COALESCE(d.demand_std, 0) * SQRT(GREATEST(l.lead_time_days, 1))
            THEN 1 ELSE 0
        END
    ) AS replenishment_skus,
    SUM(d.avg_daily_demand * 365 * l.unit_price) AS annual_revenue_proxy
FROM latest l
JOIN demand d ON d.sku_id = l.sku_id;

SELECT
    category,
    COUNT(DISTINCT sku_id) AS sku_count,
    SUM(units_on_hand * unit_cost) AS inventory_value,
    SUM(units_sold * unit_price) AS gross_sales_value,
    SUM(units_on_hand = 0) AS stockout_rows
FROM v_inventory_clean
GROUP BY category
ORDER BY inventory_value DESC;
