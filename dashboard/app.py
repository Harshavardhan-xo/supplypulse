from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analytics import build_sku_snapshot, category_summary, kpis, monthly_summary
from src.cleaning import clean_inventory
from src.data_generator import generate_raw_data
from src.forecast import forecast_sku


st.set_page_config(page_title="SupplyPulse | Inventory Control Tower", page_icon="◈", layout="wide")
st.markdown(
    """
    <style>
    .block-container{padding-top:1.1rem;max-width:1480px}
    .hero{padding:1.4rem 1.6rem;border-radius:20px;background:linear-gradient(135deg,#071b2f,#0f4c5c);color:white;margin-bottom:1rem;box-shadow:0 8px 28px rgba(8,47,73,.16)}
    .hero h1{margin:0;font-size:2.15rem}.hero p{margin:.45rem 0 0;color:#d9eef7;font-size:1rem}
    .badge{display:inline-block;background:#13a8a8;color:white;padding:.28rem .65rem;border-radius:999px;font-size:.72rem;font-weight:800;letter-spacing:.06em}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_pipeline() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
    raw = generate_raw_data()
    clean, quality = clean_inventory(raw)
    snapshot = build_sku_snapshot(clean, 0.95)
    return clean, snapshot, quality


df, snapshot, quality = load_pipeline()

st.markdown(
    '<div class="hero"><span class="badge">SUPPLY CHAIN • INVENTORY ANALYTICS</span><h1>SupplyPulse — Inventory Control Tower</h1><p>From raw daily inventory events to replenishment priorities, demand forecasts and working-capital exposure.</p></div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Portfolio Controls")
    service = st.select_slider(
        "Target service level",
        options=[0.90, 0.95, 0.99],
        value=0.95,
        format_func=lambda x: f"{x:.0%}",
    )
    categories = st.multiselect("Category", sorted(snapshot.category.unique()), default=sorted(snapshot.category.unique()))
    suppliers = st.multiselect("Supplier", sorted(snapshot.supplier.unique()), default=sorted(snapshot.supplier.unique()))
    abc = st.multiselect("ABC class", ["A", "B", "C"], default=["A", "B", "C"])
    min_days = st.number_input("Minimum days of stock", min_value=0, max_value=365, value=0, step=5)

snapshot = build_sku_snapshot(df, service)
view = snapshot[
    snapshot.category.isin(categories)
    & snapshot.supplier.isin(suppliers)
    & snapshot.abc_class.isin(abc)
    & (snapshot.days_of_stock >= min_days)
].copy()

if view.empty:
    st.warning("No SKUs match the current filters. Reduce the filter scope to continue.")
    st.stop()

m = kpis(view)
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Inventory Value", f"₹{m['inventory_value']/1e7:.2f} Cr")
c2.metric("SKUs", f"{m['skus']:,}")
c3.metric("Below Reorder", f"{m['below_reorder']:,}")
c4.metric("Overstock Value", f"₹{m['overstock_value']/1e6:.1f} M")
c5.metric("Revenue Risk", f"₹{m['stockout_revenue_risk']/1e6:.1f} M")
st.caption(
    f"Pipeline quality: {quality['output_rows']:,} clean rows • "
    f"{quality['duplicate_keys_removed']:,} duplicates removed • "
    f"service level {service:.0%}"
)

t1, t2, t3, t4, t5 = st.tabs(
    ["Executive Overview", "Replenishment", "Demand & Forecast", "Working Capital", "Data Quality"]
)

with t1:
    monthly = monthly_summary(df)
    cat = category_summary(view)
    l, r = st.columns(2)
    l.plotly_chart(
        px.line(monthly, x="month", y="sales_value", markers=True, title="Monthly Sales Value"),
        use_container_width=True,
    )
    r.plotly_chart(
        px.bar(cat, x="category", y="inventory_value", title="Inventory Value by Category", text_auto=".2s"),
        use_container_width=True,
    )
    risk = cat.sort_values("stockout_revenue_risk", ascending=False).head(7)
    st.plotly_chart(
        px.bar(
            risk,
            x="stockout_revenue_risk",
            y="category",
            orientation="h",
            title="Stockout Revenue Risk by Category",
        ),
        use_container_width=True,
    )

with t2:
    plan = view[view.stock_status == "REPLENISH"].sort_values(
        ["stockout_revenue_risk", "days_of_stock"],
        ascending=[False, True],
    )
    cols = [
        "sku_id", "category", "supplier", "abc_class", "avg_daily_demand",
        "units_on_hand", "days_of_stock", "reorder_point",
        "suggested_order_qty", "stockout_revenue_risk"
    ]
    st.dataframe(plan[cols], use_container_width=True, hide_index=True)
    st.download_button(
        "Download Replenishment Plan",
        plan[cols].to_csv(index=False).encode(),
        "supplypulse_replenishment.csv",
        "text/csv",
    )

with t3:
    sku = st.selectbox("SKU drill-down", sorted(view.sku_id.unique()))
    history = df[df.sku_id == sku].sort_values("date").tail(90)
    forecast = forecast_sku(df, int(sku), 30)
    l, r = st.columns(2)
    l.plotly_chart(
        px.line(history, x="date", y="units_sold", title=f"90-Day Demand History — SKU {sku}"),
        use_container_width=True,
    )
    r.plotly_chart(
        px.line(forecast, x="date", y="forecast_units", title="30-Day Demand Forecast"),
        use_container_width=True,
    )
    row = view[view.sku_id == sku].iloc[0]
    a, b, c, d = st.columns(4)
    a.metric("Avg / Day", f"{row.avg_daily_demand:.1f}")
    b.metric("Days of Stock", f"{row.days_of_stock:.1f}")
    c.metric("Reorder Point", f"{row.reorder_point:.0f}")
    d.metric("Suggested Order", f"{int(row.suggested_order_qty):,}")

with t4:
    by_cat = view.groupby("category", as_index=False).agg(
        inventory_value=("inventory_value", "sum"),
        overstock_value=("overstock_value", "sum"),
        stockout_risk=("stockout_revenue_risk", "sum"),
    )
    st.plotly_chart(
        px.bar(
            by_cat,
            x="category",
            y=["inventory_value", "overstock_value"],
            barmode="group",
            title="Working Capital by Category",
        ),
        use_container_width=True,
    )
    working = view.sort_values("inventory_value", ascending=False)[
        ["sku_id", "category", "abc_class", "inventory_value", "days_of_stock", "overstock_value", "stock_status"]
    ].head(50)
    st.dataframe(working, use_container_width=True, hide_index=True)

with t5:
    q = pd.DataFrame(
        [
            ["Input rows", quality["input_rows"], "Source events before cleaning"],
            ["Output rows", quality["output_rows"], "Rows available to analytics"],
            ["Duplicate keys removed", quality["duplicate_keys_removed"], "Duplicate date + SKU records"],
            ["Invalid dates", quality["null_dates"], "Rows with non-parsable date"],
            ["Stockout observations", quality["stockout_rows"], "Daily rows with zero on-hand"],
        ],
        columns=["Metric", "Value", "Definition"],
    )
    st.dataframe(q, use_container_width=True, hide_index=True)
    st.info(
        "Synthetic data is used for portfolio demonstration. Planning outputs are analytical scenarios, "
        "not live ERP replenishment instructions."
    )
