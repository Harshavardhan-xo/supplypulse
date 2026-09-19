CREATE DATABASE IF NOT EXISTS supplypulse;
USE supplypulse;

CREATE TABLE IF NOT EXISTS inventory_daily (
    inventory_date DATE NOT NULL,
    sku_id BIGINT NOT NULL,
    category VARCHAR(50) NOT NULL,
    supplier VARCHAR(100) NOT NULL,
    region VARCHAR(30) NOT NULL,
    unit_cost DECIMAL(12,2) NOT NULL,
    unit_price DECIMAL(12,2) NOT NULL,
    lead_time_days INT NOT NULL,
    opening_stock INT NOT NULL,
    units_received INT NOT NULL,
    units_sold INT NOT NULL,
    units_on_hand INT NOT NULL,
    PRIMARY KEY (inventory_date, sku_id),
    INDEX idx_inventory_sku (sku_id),
    INDEX idx_inventory_category (category)
);

CREATE OR REPLACE VIEW v_inventory_quality AS
SELECT
    COUNT(*) AS row_count,
    COUNT(DISTINCT sku_id) AS sku_count,
    MIN(inventory_date) AS min_date,
    MAX(inventory_date) AS max_date,
    SUM(units_on_hand = 0) AS stockout_rows
FROM inventory_daily;
