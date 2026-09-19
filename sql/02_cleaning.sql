USE supplypulse;

CREATE OR REPLACE VIEW v_inventory_clean AS
SELECT
    inventory_date,
    sku_id,
    NULLIF(TRIM(category), '') AS category,
    NULLIF(TRIM(supplier), '') AS supplier,
    NULLIF(TRIM(region), '') AS region,
    GREATEST(unit_cost, 0) AS unit_cost,
    GREATEST(unit_price, 0) AS unit_price,
    GREATEST(lead_time_days, 0) AS lead_time_days,
    GREATEST(opening_stock, 0) AS opening_stock,
    GREATEST(units_received, 0) AS units_received,
    GREATEST(units_sold, 0) AS units_sold,
    GREATEST(units_on_hand, 0) AS units_on_hand,
    GREATEST(units_sold, 0) * GREATEST(unit_price, 0) AS gross_sales_value,
    GREATEST(units_on_hand, 0) * GREATEST(unit_cost, 0) AS inventory_value
FROM inventory_daily;
