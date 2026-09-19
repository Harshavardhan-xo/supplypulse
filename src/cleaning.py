from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = [
    "date", "sku_id", "category", "supplier", "region", "unit_cost", "unit_price",
    "lead_time_days", "opening_stock", "units_received", "units_sold", "units_on_hand",
]


def clean_inventory(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Clean the raw inventory table and return a compact quality report."""
    missing_required = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_required:
        raise ValueError(f"Missing required columns: {missing_required}")

    work = df.copy()
    original_rows = len(work)
    work["date"] = pd.to_datetime(work["date"], errors="coerce")

    numeric = [
        "sku_id", "unit_cost", "unit_price", "lead_time_days", "opening_stock",
        "units_received", "units_sold", "units_on_hand",
    ]
    for col in numeric:
        work[col] = pd.to_numeric(work[col], errors="coerce")

    null_dates = int(work["date"].isna().sum())
    work = work.dropna(subset=["date", "sku_id"]).copy()
    rows_after_required = len(work)

    duplicates = int(work.duplicated(subset=["date", "sku_id"]).sum())
    work = work.sort_values(["sku_id", "date"]).drop_duplicates(["date", "sku_id"], keep="last")

    for col in ["unit_cost", "unit_price", "lead_time_days", "opening_stock", "units_received", "units_sold", "units_on_hand"]:
        work[col] = work[col].clip(lower=0)

    category_mode = work["category"].mode().iat[0] if not work["category"].dropna().empty else "Unknown"
    supplier_mode = work["supplier"].mode().iat[0] if not work["supplier"].dropna().empty else "Unknown"
    region_mode = work["region"].mode().iat[0] if not work["region"].dropna().empty else "Unknown"
    work["category"] = work["category"].fillna(category_mode)
    work["supplier"] = work["supplier"].fillna(supplier_mode)
    work["region"] = work["region"].fillna(region_mode)

    for col in ["unit_cost", "unit_price", "lead_time_days"]:
        work[col] = work[col].fillna(work[col].median())
    for col in ["opening_stock", "units_received", "units_sold", "units_on_hand"]:
        work[col] = work[col].fillna(0)

    work["gross_sales_value"] = work["units_sold"] * work["unit_price"]
    work["inventory_value"] = work["units_on_hand"] * work["unit_cost"]
    work["stockout_flag"] = work["units_on_hand"].eq(0).astype(int)

    quality = {
        "input_rows": int(original_rows),
        "rows_removed_bad_date_or_id": int(original_rows - rows_after_required),
        "duplicate_keys_removed": duplicates,
        "null_dates": null_dates,
        "output_rows": int(len(work)),
        "stockout_rows": int(work["stockout_flag"].sum()),
    }
    return work, quality
