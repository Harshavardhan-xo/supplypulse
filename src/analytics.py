from __future__ import annotations

import math

import numpy as np
import pandas as pd

Z_BY_SERVICE = {0.90: 1.2816, 0.95: 1.6449, 0.99: 2.3263}


def _z_value(service_level: float) -> float:
    return float(Z_BY_SERVICE[min(Z_BY_SERVICE, key=lambda x: abs(x - service_level))])


def build_sku_snapshot(df: pd.DataFrame, service_level: float = 0.95) -> pd.DataFrame:
    """Build a point-in-time SKU planning table using the trailing 28/30 days."""
    latest = df["date"].max()
    recent_28 = df[df["date"] > latest - pd.Timedelta(days=28)]
    recent_30 = df[df["date"] > latest - pd.Timedelta(days=30)]

    demand = recent_28.groupby("sku_id")["units_sold"].mean().rename("avg_daily_demand")
    demand_std = recent_30.groupby("sku_id")["units_sold"].std(ddof=0).fillna(0).rename("demand_std")

    cols = ["sku_id", "category", "supplier", "region", "unit_cost", "unit_price", "lead_time_days", "units_on_hand"]
    latest_rows = (
        df.sort_values("date")
        .groupby("sku_id", as_index=False)
        .tail(1)[cols]
        .set_index("sku_id")
    )
    out = latest_rows.join(demand, how="left").join(demand_std, how="left").fillna({"avg_daily_demand": 0, "demand_std": 0})
    z = _z_value(service_level)
    out["safety_stock"] = z * out["demand_std"] * np.sqrt(out["lead_time_days"].clip(lower=1))
    out["reorder_point"] = out["avg_daily_demand"] * out["lead_time_days"] + out["safety_stock"]
    out["days_of_stock"] = np.where(out["avg_daily_demand"] > 0, out["units_on_hand"] / out["avg_daily_demand"], np.inf)
    out["suggested_order_qty"] = np.maximum(0, np.ceil(out["reorder_point"] - out["units_on_hand"]))
    out["inventory_value"] = out["units_on_hand"] * out["unit_cost"]
    out["stockout_revenue_risk"] = np.maximum(out["reorder_point"] - out["units_on_hand"], 0) * out["unit_price"]
    out["overstock_units"] = np.maximum(out["units_on_hand"] - out["avg_daily_demand"] * 90, 0)
    out["overstock_value"] = out["overstock_units"] * out["unit_cost"]
    out["annual_revenue_proxy"] = out["avg_daily_demand"] * 365 * out["unit_price"]

    rank = out["annual_revenue_proxy"].rank(method="first", ascending=False)
    out["abc_class"] = pd.cut(
        rank,
        bins=[0, math.ceil(len(out) * 0.20), math.ceil(len(out) * 0.50), len(out) + 1],
        labels=["A", "B", "C"],
        include_lowest=True,
    ).astype(str)
    out["stock_status"] = np.select(
        [out["units_on_hand"] <= out["reorder_point"], out["days_of_stock"] > 90],
        ["REPLENISH", "OVERSTOCK"],
        default="HEALTHY",
    )
    return out.reset_index()


def kpis(snapshot: pd.DataFrame) -> dict[str, float | int]:
    return {
        "inventory_value": float(snapshot["inventory_value"].sum()),
        "skus": int(snapshot["sku_id"].nunique()),
        "below_reorder": int((snapshot["stock_status"] == "REPLENISH").sum()),
        "overstock_value": float(snapshot["overstock_value"].sum()),
        "stockout_revenue_risk": float(snapshot["stockout_revenue_risk"].sum()),
        "portfolio_revenue_proxy": float(snapshot["annual_revenue_proxy"].sum()),
    }


def category_summary(snapshot: pd.DataFrame) -> pd.DataFrame:
    out = (
        snapshot.groupby("category", as_index=False)
        .agg(
            skus=("sku_id", "nunique"),
            inventory_value=("inventory_value", "sum"),
            revenue_proxy=("annual_revenue_proxy", "sum"),
            overstock_value=("overstock_value", "sum"),
            stockout_revenue_risk=("stockout_revenue_risk", "sum"),
        )
        .sort_values("revenue_proxy", ascending=False)
    )
    out["risk_rate"] = out["stockout_revenue_risk"] / out["revenue_proxy"].replace(0, np.nan)
    return out


def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    work["month"] = work["date"].dt.to_period("M").astype(str)
    return (
        work.groupby("month", as_index=False)
        .agg(
            units_sold=("units_sold", "sum"),
            sales_value=("gross_sales_value", "sum"),
            avg_on_hand=("units_on_hand", "mean"),
            stockout_rows=("stockout_flag", "sum"),
        )
    )
