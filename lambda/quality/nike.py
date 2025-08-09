# quality/nike.py

import json
import pandas as pd
from logger import logger

_REQUIRED = [
    "id","title","subTitle","url","image",
    "price_sale","price_original","gender","age_group","brand","extra"
]

class NikeQuality:
    def test_required_columns(self, df: pd.DataFrame) -> bool:
        missing = [c for c in _REQUIRED if c not in df.columns]
        if missing:
            logger.error(f"Missing columns: {missing}")
        return not missing

    def test_prices(self, df: pd.DataFrame) -> bool:
        ok = True
        for c in ("price_sale","price_original"):
            if df[c].isnull().any():
                logger.error(f"{c} has nulls"); ok = False
            if not pd.api.types.is_numeric_dtype(df[c]):
                logger.error(f"{c} not numeric"); ok = False
            if (df[c] < 0).any():
                logger.error(f"{c} has negatives"); ok = False
        return ok

    def test_gender_list(self, df: pd.DataFrame) -> bool:
        if "gender" not in df.columns:
            logger.error("missing 'gender' column"); return False
        bad = df[~df["gender"].apply(lambda g: isinstance(g, list))]
        if len(bad):
            logger.error(f"{len(bad)} rows have non-list gender")
            return False
        return True

    def test_extra_json(self, df: pd.DataFrame) -> bool:
        ok = True
        for idx, val in df["extra"].dropna().items():
            try:
                obj = json.loads(val)
            except Exception:
                logger.error(f"row {idx} extra not valid JSON: {val}")
                ok = False; continue
            if not isinstance(obj, dict) or "category" not in obj or "sizes" not in obj:
                logger.error(f"row {idx} extra missing keys: {obj}")
                ok = False
        return ok

    def run(self, df: pd.DataFrame) -> (bool, dict):
        logger.info("Running Nike data-quality tests...")
        results = {
            "required_columns": self.test_required_columns(df),
            "prices_ok":        self.test_prices(df),
            "gender_is_list":   self.test_gender_list(df),
            "extra_valid":      self.test_extra_json(df),
        }
        overall = all(results.values())
        for k, v in results.items():
            logger.info(f"{k}: {'PASS' if v else 'FAIL'}")
        logger.info(f"OVERALL: {'PASS' if overall else 'FAIL'}")
        return overall, results
