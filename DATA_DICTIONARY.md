# SupplyPulse — Data Dictionary

| Field | Type | Description |
|---|---|---|
| date / inventory_date | DATE | Daily observation date |
| sku_id | BIGINT | Unique stock-keeping unit identifier |
| category | TEXT | Merchandise category |
| supplier | TEXT | Supplier name |
| region | TEXT | Operating region |
| unit_cost | DECIMAL | Unit procurement cost |
| unit_price | DECIMAL | Selling price per unit |
| lead_time_days | INT | Supplier lead time in days |
| opening_stock | INT | Stock available at the beginning of the day |
| units_received | INT | Units received during the day |
| units_sold | INT | Units sold during the day |
| units_on_hand | INT | End-of-day stock balance |
| gross_sales_value | DECIMAL | Units sold × unit price |
| inventory_value | DECIMAL | Units on hand × unit cost |
| avg_daily_demand | DECIMAL | Trailing 28-day average units sold |
| demand_std | DECIMAL | Trailing 30-day demand variability |
| reorder_point | DECIMAL | Lead-time demand plus safety stock |
| days_of_stock | DECIMAL | On-hand quantity / average daily demand |
| suggested_order_qty | INT | Recommended replenishment quantity |
| abc_class | TEXT | Revenue-proxy concentration class A/B/C |
| stock_status | TEXT | HEALTHY, REPLENISH or OVERSTOCK |
