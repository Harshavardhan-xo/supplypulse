# SupplyPulse

### Inventory Control Tower

**[Open Live Dashboard ↗](https://harsha-supplypulse.streamlit.app)**

Built around **500 SKUs and 182,500 daily inventory/sales observations** to demonstrate inventory planning at portfolio scale.

## Key capabilities

- ABC segmentation using trailing revenue proxy
- Service-level driven reorder-point logic
- Stockout revenue-risk and overstock working-capital views
- 90-day demand history and 30-day forecast drill-down
- Replenishment workbench with downloadable order plan
- Category filters and portfolio-level KPIs

## Reorder logic

`reorder point = forecast demand × lead time + safety stock`

`safety stock = z(service level) × demand variability × √lead time`

Default service level is 95%.

## Data disclosure

Synthetic data only. The dashboard is a planning demonstration, not a replacement for an enterprise WMS/ERP replenishment engine.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```
