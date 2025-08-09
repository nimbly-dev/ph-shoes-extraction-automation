# quality/hoka.py

import json
import pandas as pd
from logger import logger
from clean.hoka import HokaCleaner

REQUIRED_COLS = [
    "id", "title", "subTitle", "url", "image",
    "price_sale", "price_original", "gender", "age_group", "brand", "extra"
]

SIZE_SET = {
    "6","6.5","7","7.5","8","8.5","9","9.5","10","10.5","11","11.5","12","13"
}

class HokaQuality:
    """
    Data-quality tests for Hoka cleaned DataFrame.
    """

    def __init__(self):
        self.cleaner = HokaCleaner()

    # --- small unit checks used in run() ---

    def test_required_columns(self, df: pd.DataFrame) -> bool:
        return all(c in df.columns for c in REQUIRED_COLS)

    def test_prices_numeric(self, df: pd.DataFrame) -> bool:
        return all(pd.api.types.is_numeric_dtype(df[c]) for c in ["price_sale","price_original"])

    def test_no_missing_ids(self, df: pd.DataFrame) -> bool:
        return df["id"].notna().all()

    def test_gender_list(self, df: pd.DataFrame) -> bool:
        if "gender" not in df.columns:
            return False
        return df["gender"].apply(lambda g: isinstance(g, list)).all()

    def test_extra_valid(self, df: pd.DataFrame) -> bool:
        for idx, val in df["extra"].dropna().items():
            try:
                obj = json.loads(val)
            except Exception:
                logger.error(f"Row {idx}: extra is not valid JSON: {val}")
                return False
            if "category" not in obj or "sizes" not in obj:
                logger.error(f"Row {idx}: extra missing keys: {obj}")
                return False
            if not isinstance(obj["sizes"], list):
                logger.error(f"Row {idx}: extra.sizes is not a list")
                return False
            # sizes must be from allowed set (if present)
            if any(str(s) not in SIZE_SET for s in obj["sizes"]):
                logger.error(f"Row {idx}: unexpected size values: {obj['sizes']}")
                return False
        return True

    def run(self, df: pd.DataFrame) -> (bool, dict):
        logger.info("Running Hoka data-quality tests...")
        results = {
            "required_columns":   bool(self.test_required_columns(df)),
            "prices_numeric":     bool(self.test_prices_numeric(df)),
            "no_missing_ids":     bool(self.test_no_missing_ids(df)),
            "gender_is_list":     bool(self.test_gender_list(df)),
            "extra_valid_json":   bool(self.test_extra_valid(df)),
        }
        overall = all(results.values())

        for name, ok in results.items():
            logger.info(f"{name}: {'PASS' if ok else 'FAIL'}")
        logger.info(f"OVERALL: {'PASS' if overall else 'FAIL'}")

        return bool(overall), results
