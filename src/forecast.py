from __future__ import annotations

import pandas as pd
from statsmodels.tsa.holtwinters import SimpleExpSmoothing


def forecast_sku(df: pd.DataFrame, sku_id: int, horizon: int = 30) -> pd.DataFrame:
    work = df[df["sku_id"] == sku_id].sort_values("date")
    if work.empty:
        raise ValueError(f"Unknown SKU: {sku_id}")
    series = work.set_index("date")["units_sold"].astype(float).asfreq("D").fillna(0)
    if len(series) < 14 or series.sum() == 0:
        value = float(series.tail(14).mean()) if len(series) else 0.0
        future = pd.Series([value] * horizon)
    else:
        model = SimpleExpSmoothing(series, initialization_method="estimated").fit(optimized=True)
        future = model.forecast(horizon)
    start = pd.to_datetime(work["date"].max()) + pd.Timedelta(days=1)
    return pd.DataFrame({"date": pd.date_range(start, periods=horizon), "forecast_units": future.to_numpy()})
