# quality/nike.py

import json
import pandas as pd
from logger import logger

class NikeQuality:
    """
    Data-quality tests for Nike cleaned DataFrame, including checks
    for the new `extra` JSON field.
    """

    def test_no_null_prices(self, df: pd.DataFrame) -> bool:
        ok = True
        for c in ["price_sale", "price_original"]:
            n = df[c].isnull().sum()
            if n:
                logger.error(f"Test Failed: {c} has {n} null(s).")
                ok = False
        return ok

    def test_gender_list(self, df: pd.DataFrame) -> bool:
        ok = True
        if "gender" not in df.columns:
            logger.error("Test Failed: missing 'gender' column")
            return False
        for idx, g in df["gender"].items():
            if not isinstance(g, list):
                logger.error(f"Test Failed: id={df.at[idx,'id']} gender not list: {g!r}")
                ok = False
        return ok

    def test_subtitle_and_extra(self, df: pd.DataFrame) -> bool:
        # Ensure subTitle and extra columns exist
        if "subTitle" not in df.columns or "extra" not in df.columns:
            logger.error("Test Failed: missing 'subTitle' or 'extra' column")
            return False
        return True

    def test_extra_valid_json(self, df: pd.DataFrame) -> bool:
        ok = True
        for idx, val in df["extra"].dropna().items():
            try:
                obj = json.loads(val)
            except Exception:
                logger.error(f"Test Failed: row {idx} extra not valid JSON: {val}")
                return False
            # you can add further key‐existence tests here if desired
        return ok

    def test_negative_prices(self, df: pd.DataFrame) -> bool:
        ok = True
        for idx, row in df.iterrows():
            for c in ["price_sale", "price_original"]:
                if row[c] < 0:
                    logger.error(f"Test Failed: id={row['id']} negative {c}: {row[c]}")
                    ok = False
        return ok

    def run(self, df: pd.DataFrame) -> (bool, dict):
        logger.info("Running Nike data-quality tests...")
        results = {
            "no_null_prices":     bool(self.test_no_null_prices(df)),
            "gender_list":        bool(self.test_gender_list(df)),
            "subtitle_and_extra": bool(self.test_subtitle_and_extra(df)),
            "extra_valid_json":   bool(self.test_extra_valid_json(df)),
            "non_negative_prices":bool(self.test_negative_prices(df)),
        }
        overall = all(results.values())

        for name, passed in results.items():
            logger.info(f"{name}: {'PASS' if passed else 'FAIL'}")
        logger.info(f"OVERALL: {'PASS' if overall else 'FAIL'}")

        return overall, results
