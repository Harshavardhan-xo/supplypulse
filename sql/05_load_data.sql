USE supplypulse;

-- Generate the CSV first:
-- python data/generate_raw_data.py
--
-- Then load it from a trusted local path. LOCAL INFILE may need to be enabled
-- in both the MySQL client and server configuration.
LOAD DATA LOCAL INFILE 'data/raw_inventory_daily.csv'
INTO TABLE inventory_daily
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
IGNORE 1 ROWS
(@inventory_date, sku_id, category, supplier, region, unit_cost, unit_price,
 lead_time_days, opening_stock, units_received, units_sold, units_on_hand)
SET inventory_date = STR_TO_DATE(@inventory_date, '%Y-%m-%d');
