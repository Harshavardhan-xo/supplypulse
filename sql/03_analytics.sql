USE supplypulse;

WITH latest AS (
    SELECT MAX(inventory_date) AS latest_date FROM v_inventory_clean
),
recent AS (
    SELECT i.*
    FROM v_inventory_clean i
    CROSS JOIN latest l
    WHERE i.inventory_date > l.latest_date - INTERVAL 28 DAY
),
demand AS (
    SELECT
        sku_id,
        AVG(units_sold) AS avg_daily_demand,
        STDDEV_POP(units_sold) AS demand_std
    FROM recent
    GROUP BY sku_id
),
last_row AS (
    SELECT *
    FROM (
        SELECT i.*, ROW_NUMBER() OVER (PARTITION BY sku_id ORDER BY inventory_date DESC) AS rn
        FROM v_inventory_clean i
    ) x
    WHERE rn = 1
)
SELECT
    l.sku_id,
    l.category,
    l.supplier,
    l.region,
    l.unit_cost,
    l.unit_price,
    l.lead_time_days,
    l.units_on_hand,
    COALESCE(d.avg_daily_demand, 0) AS avg_daily_demand,
    COALESCE(d.demand_std, 0) AS demand_std,
    COALESCE(d.avg_daily_demand, 0) * l.lead_time_days
        + 1.6449 * COALESCE(d.demand_std, 0) * SQRT(GREATEST(l.lead_time_days, 1)) AS reorder_point,
    l.units_on_hand * l.unit_cost AS inventory_value
FROM last_row l
LEFT JOIN demand d ON d.sku_id = l.sku_id;
