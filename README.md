# SupplyPulse — Inventory Control Tower

SupplyPulse is a business-focused inventory analytics portfolio project built as an end-to-end workflow:

**Excel → MySQL/SQL → Python (NumPy + Pandas) → Forecasting → Streamlit dashboard**

## Business problem

Inventory teams need to balance three competing outcomes:

1. Maintain service levels and avoid stockouts.
2. Avoid excess inventory and tied-up working capital.
3. Prioritize replenishment decisions using demand and lead-time signals.

## What this project demonstrates

- Excel-based operational analysis and KPI design
- MySQL schema, cleaning views, CTEs and window functions
- Python data cleaning with Pandas
- Vectorized numerical calculations with NumPy
- ABC inventory classification
- Reorder-point and safety-stock logic
- 30-day demand forecasting
- Working-capital and revenue-at-risk analysis
- Executive Streamlit dashboard with drill-downs and downloadable plans
- Unit-tested analytical pipeline

## Project structure

~~~text
SupplyPulse/
├── app.py
├── BUSINESS_REQUIREMENTS.md
├── DATA_DICTIONARY.md
├── data/
│   └── generate_raw_data.py
├── dashboard/
│   └── app.py
├── excel/
│   └── README.md
├── sql/
│   ├── 01_schema.sql
│   ├── 02_cleaning.sql
│   ├── 03_analytics.sql
│   ├── 04_business_kpis.sql
│   └── 05_load_data.sql
├── src/
│   ├── analytics.py
│   ├── cleaning.py
│   ├── data_generator.py
│   └── forecast.py
├── tests/
│   └── test_pipeline.py
├── requirements.txt
└── requirements-dev.txt
~~~

## Data disclosure

All data is synthetic and generated deterministically from src/data_generator.py. No real company, customer, supplier or employee data is used.

## Run locally

~~~bash
pip install -r requirements.txt
python data/generate_raw_data.py
streamlit run app.py
~~~

## Run tests

~~~bash
pip install -r requirements-dev.txt
pytest -q
~~~

## Replenishment logic

~~~text
Reorder Point = Forecast Demand × Lead Time + Safety Stock
Safety Stock = z(service level) × Demand Variability × √Lead Time
Suggested Order = max(0, Reorder Point − On Hand)
~~~

The dashboard uses a 95% default service level and lets the analyst switch between 90%, 95% and 99% sensitivity scenarios.

## Excel deliverable

A polished SupplyPulse_Analysis.xlsx workbook is provided alongside the repository. It contains a representative 120-SKU × 60-day sample with data-quality checks, formula-driven SKU analysis, category analysis and an executive dashboard.
