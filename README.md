# SupplyPulse
### Inventory Health & Stockout-Risk Dashboard

Run:
```bash
pip install -r requirements.txt
streamlit run app.py
```

The app generates a reproducible 150-SKU daily sales history, forecasts demand with Simple Exponential Smoothing, and calculates reorder points using a 95% default service level. Synthetic-data limitations are disclosed in the dashboard.