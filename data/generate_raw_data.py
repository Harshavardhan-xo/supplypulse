from pathlib import Path

from src.data_generator import save_raw_data


if __name__ == "__main__":
    save_raw_data(Path(__file__).resolve().parent / "raw_inventory_daily.csv")
