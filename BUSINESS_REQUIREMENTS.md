# SupplyPulse — Business Requirements

## Business objective

Provide an inventory-control workflow that helps an operations analyst identify:

- which SKUs are below a target service-level reorder point;
- where working capital is concentrated in slow-moving stock;
- which categories carry the highest stockout revenue exposure; and
- how recent demand translates into a practical replenishment queue.

## Key business questions

1. How much cash is currently tied up in inventory?
2. Which SKUs should be replenished first?
3. Which SKUs are at risk of stockout before the supplier lead time is covered?
4. Where is inventory sitting above a 90-day coverage threshold?
5. How does the result change at 90%, 95% and 99% service-level assumptions?
6. What does recent demand imply for the next 30 days?

## KPI definitions

| KPI | Definition |
|---|---|
| Inventory Value | Units on hand × unit cost |
| Average Daily Demand | Mean units sold during the trailing 28 days |
| Demand Variability | Population standard deviation during the trailing 30 days |
| Safety Stock | z(service level) × demand variability × √lead time |
| Reorder Point | Average daily demand × lead time + safety stock |
| Days of Stock | Units on hand ÷ average daily demand |
| Suggested Order Qty | MAX(0, reorder point − units on hand) |
| Overstock Value | Units above 90-day coverage × unit cost |
| Stockout Revenue Risk | Units required to reach reorder point × unit price |
