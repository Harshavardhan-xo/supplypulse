from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

CATEGORIES = ["Grocery", "Beauty", "Home", "Electronics", "Fashion", "Pet", "Health"]
SUPPLIERS = ["Alpha Supply", "BlueRiver", "CoreTrade", "Delta Wholesale", "Evergreen", "FreshRoute"]
REGIONS = ["South", "West", "North", "East"]


def generate_raw_data(n_skus: int = 500, days: int = 365, seed: int = 19) -> pd.DataFrame:
    """Generate deterministic synthetic daily inventory transactions."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=days, freq="D")
    sku = np.arange(100001, 100001 + n_skus)

    meta = pd.DataFrame(
        {
            "sku_id": sku,
            "category": rng.choice(CATEGORIES, n_skus),
            "supplier": rng.choice(SUPPLIERS, n_skus),
            "region": rng.choice(REGIONS, n_skus, p=[0.30, 0.25, 0.25, 0.20]),
            "unit_cost": rng.uniform(25, 1800, n_skus).round(2),
            "unit_price": 0.0,
            "lead_time_days": rng.integers(2, 22, n_skus),
        }
    )
    meta["unit_price"] = (meta["unit_cost"] * rng.uniform(1.22, 2.25, n_skus)).round(2)
    meta["base_daily_demand"] = rng.lognormal(mean=2.3, sigma=0.8, size=n_skus)
    meta["seasonality_phase"] = rng.uniform(0, 2 * np.pi, n_skus)

    rows: list[list[object]] = []
    t = np.arange(days)
    for _, row in meta.iterrows():
        seasonal = 1 + 0.28 * np.sin(t / 365 * 2 * np.pi + row["seasonality_phase"])
        trend = np.linspace(1.0, rng.uniform(0.88, 1.12), days)
        weekday = np.where(pd.Series(dates).dt.dayofweek.to_numpy() >= 4, 1.08, 0.97)
        lam = np.maximum(row["base_daily_demand"] * seasonal * trend * weekday, 0.1)
        units_sold = rng.poisson(lam)

        opening = max(20, int(row["base_daily_demand"] * row["lead_time_days"] * rng.uniform(2.5, 4.5)))
        on_hand = opening
        for d, sold in zip(dates, units_sold):
            beginning = on_hand
            received = 0
            on_hand = max(0, on_hand - int(sold))
            reorder_trigger = row["base_daily_demand"] * row["lead_time_days"] * 1.2
            if on_hand < reorder_trigger:
                received = int(row["base_daily_demand"] * row["lead_time_days"] * rng.uniform(2, 4))
                on_hand += received
            rows.append(
                [
                    d,
                    int(row["sku_id"]),
                    row["category"],
                    row["supplier"],
                    row["region"],
                    float(row["unit_cost"]),
                    float(row["unit_price"]),
                    int(row["lead_time_days"]),
                    int(beginning),
                    int(received),
                    int(sold),
                    int(on_hand),
                ]
            )

    return pd.DataFrame(
        rows,
        columns=[
            "date", "sku_id", "category", "supplier", "region",
            "unit_cost", "unit_price", "lead_time_days",
            "opening_stock", "units_received", "units_sold", "units_on_hand",
        ],
    )


def save_raw_data(output_path: str | Path, **kwargs: object) -> pd.DataFrame:
    df = generate_raw_data(**kwargs)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return df


if __name__ == "__main__":
    save_raw_data(Path(__file__).resolve().parents[1] / "data" / "raw_inventory_daily.csv")
