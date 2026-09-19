# SupplyPulse
### Inventory Health & Stockout-Risk Dashboard

> **How to use this document:** Paste this whole file into ChatGPT as your
> first message and ask it to build the project exactly as specified below,
> file by file, in the order given in Section 11.

## 1. Business Problem
Retail/e-commerce ops teams sit between two costly failure modes: stockouts
(lost sales, unhappy customers) and overstock (cash tied up in slow-moving
inventory). Without a systematic reorder signal, both happen constantly
across hundreds of SKUs. Ops needs a prioritized list of what to reorder,
when, and how much.

**Business questions this project answers:**
- Which SKUs are about to stock out, given current demand and lead time?
- Which SKUs are overstocked and tying up working capital?
- What's the reorder point and suggested order quantity per SKU?

## 2. Business Impact
Converts raw sales/inventory logs into a specific, actionable reorder list
with a $ estimate of risk — exactly the kind of ops-facing deliverable a
retail/supply-chain BA is hired to produce.

## 3. Solution Overview
Synthetic SKU, sales, and inventory data in SQLite; SQL views for ABC
classification and inventory aging; a Python forecasting layer (exponential
smoothing via statsmodels) computing a reorder point per SKU; a Streamlit
dashboard flagging at-risk and overstocked SKUs.

## 4. Tech Stack
| Layer | Tool | Purpose |
|---|---|---|
| Language | Python 3.11+ | Core logic |
| Database | SQLite | Local relational store |
| Query layer | SQL | ABC classification, inventory aging |
| Forecasting | statsmodels (Simple Exponential Smoothing) | Per-SKU demand forecast |
| Data handling | pandas, numpy | Transformation |
| App/dashboard | Streamlit | Interactive UI |
| Charts | Plotly | ABC chart, demand-vs-forecast per SKU |
| Testing | pytest | Unit tests |
| Version control | Git + GitHub | Source control |

## 5. Architecture / Pipeline
```
[generate_synthetic_data.py] --> [SQLite: supplypulse.db]
        v
[queries/abc_classification.sql] --> ABC tier per SKU
        v
[forecasting.py] -- exponential smoothing --> forecasted daily demand,
                                                demand variability per SKU
        v
[reorder point = avg_daily_demand * lead_time_days + safety_stock]
        v
[metrics.py] --> KPI summary (SKUs below reorder point, $ overstocked, etc.)
        v
[app.py: Streamlit] --> KPI cards, ABC chart, reorder table, per-SKU chart
```
**Ingest (synthetic generator) → Store (SQLite) → Transform (SQL ABC/aging)
→ Model (forecast + reorder formula) → Visualize (Streamlit) → Recommend
(reorder-flagged table)**

## 6. Data Model
**`skus`**
| Column | Type |
|---|---|
| sku_id | TEXT PK |
| category | TEXT |
| unit_cost | REAL |
| unit_price | REAL |
| lead_time_days | INTEGER |

**`daily_sales`**
| Column | Type |
|---|---|
| sku_id | TEXT FK |
| date | DATE |
| units_sold | INTEGER |

**`inventory_snapshots`**
| Column | Type |
|---|---|
| sku_id | TEXT FK |
| date | DATE |
| units_on_hand | INTEGER |

## 7. Synthetic Data Generation Rules
- ~150 SKUs across 5–6 categories, 12 months of daily sales
- Mix of fast movers (high, steady demand), seasonal movers (a demand bump in
  specific months), and slow movers (sparse, low demand) so ABC
  classification produces a realistic spread
- `units_on_hand` decreases with sales and jumps up at simulated periodic
  reorder events, so some SKUs realistically dip below their reorder point
  during the series

## 8. Modeling Details
- **ABC classification (SQL):** rank SKUs by trailing-12-month revenue;
  A = top 20% of revenue, B = next 30%, C = remaining 50%
- **Forecast (Python):**
  `statsmodels.tsa.holtwinters.SimpleExpSmoothing` per SKU on daily
  units_sold → `forecasted_daily_demand`; also compute demand std-dev over
  the trailing 30 days
- **Reorder point formula:**
  `reorder_point = (forecasted_daily_demand × lead_time_days) + safety_stock`
  `safety_stock = z_score(service_level) × demand_std_dev × sqrt(lead_time_days)`
  — document this formula and its service-level assumption explicitly, both
  in code comments and the README (default 95% service level)
- **Overstock flag:** `days_of_stock = units_on_hand /
  forecasted_daily_demand`; flag as overstocked if `days_of_stock > 90`

## 9. Dashboard Specification
- **Sidebar:** category filter, service-level slider (default 95%)
- **KPI row:** # SKUs below reorder point, $ tied up in overstocked SKUs,
  estimated stockout revenue risk, total SKUs tracked
- **Chart 1:** ABC bar/pie — revenue share by tier
- **Table:** reorder-flagged SKUs — sku_id, category, days_of_stock,
  reorder_point, suggested_order_qty, sorted by urgency
- **Chart 2:** per-SKU line chart (selectable from a dropdown) — actual
  daily sales vs. forecast

## 10. File & Folder Structure
```
supplypulse/
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── data/
│   └── generate_synthetic_data.py
├── tests/
│   ├── test_forecasting.py
│   └── test_metrics.py
├── queries/
│   └── abc_classification.sql
└── src/
    ├── __init__.py
    ├── db.py
    ├── forecasting.py
    └── metrics.py
```

## 11. Step-by-Step Build Order
1. Scaffold folders; `.gitignore`, `LICENSE`.
2. Write `data/generate_synthetic_data.py` per Section 7; populates
   `supplypulse.db`.
3. Write `src/db.py`: connection + query helpers.
4. Write `queries/abc_classification.sql`.
5. Write `src/forecasting.py`: `forecast_sku(sales_series) -> (forecast,
   std_dev)` and `reorder_point(forecast, std_dev, lead_time,
   service_level) -> float` implementing Section 8's formulas exactly, with
   a small z-score lookup table for common service levels (90/95/99%).
6. Write `src/metrics.py`: KPI roll-up across all SKUs.
7. Write `tests/`: assert reorder_point increases with lead_time_days and
   with demand variability (holding other inputs fixed); assert a SKU with
   zero recent sales doesn't cause a divide-by-zero in days_of_stock.
8. Write `app.py` wiring db → forecasting → metrics → dashboard (Section 9).
9. Run locally, fix all exceptions.
10. Write final `README.md` per Section 14.
11. `git init`, commit, push.

## 12. Production-Quality Bar
- [ ] Type hints + docstrings, especially on the reorder-point formula
- [ ] No bare `except:`
- [ ] Divide-by-zero guarded everywhere demand appears in a denominator
- [ ] `logging` on the forecasting step (log any SKU that fails to fit and
  why)
- [ ] `pytest` passes
- [ ] `requirements.txt` pinned
- [ ] Zero unhandled exceptions across all 150 SKUs

## 13. Roadmap / Future Enhancements
- Swap simple exponential smoothing for Holt-Winters to capture seasonality
  explicitly
- Add a supplier lead-time variability field and propagate it into the
  safety-stock formula
- Recreate the reorder-flagged table in Power BI/Tableau connected to the
  same SQLite file
- Add a "what-if" lead-time slider showing how reorder points shift if a
  supplier gets faster/slower

## 14. Required Contents of Final `README.md`
Business problem → the reorder-point formula spelled out with its
assumptions → tech stack → setup steps → schema summary → limitations
(synthetic data, single-echelon inventory model, no supplier variability).

## 15. Definition of Done
- [ ] Forecast + reorder point compute for all 150 SKUs without error
- [ ] Reorder-flagged table and ABC chart both render and re-filter by
  category
- [ ] Tests pass
- [ ] README complete

## 16. Resume Bullet Template
"Built an inventory analytics pipeline (SQL, Python/statsmodels, Streamlit)
forecasting demand and reorder points across 150 SKUs, flagging $[X] in
overstock and [Y] SKUs at stockout risk."