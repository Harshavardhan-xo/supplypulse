from src.analytics import build_sku_snapshot, kpis
from src.cleaning import clean_inventory
from src.data_generator import generate_raw_data


def test_pipeline_contract():
    raw = generate_raw_data(n_skus=25, days=45, seed=7)
    clean, quality = clean_inventory(raw)
    snapshot = build_sku_snapshot(clean, service_level=0.95)
    metrics = kpis(snapshot)

    assert quality["output_rows"] > 0
    assert snapshot["sku_id"].nunique() == 25
    assert (snapshot["reorder_point"] >= 0).all()
    assert metrics["skus"] == 25
