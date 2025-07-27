# quality/world_balance.py

import json
import pandas as pd
from logger import logger

class WorldBalanceQuality:
    """
    Data-quality tests for WorldBalance cleaned DataFrame.
    """

    def test_price_nulls(self, df: pd.DataFrame) -> bool:
        nulls = {c: df[c].isnull().sum() for c in ("price_original","price_sale")}
        ok = all(v == 0 for v in nulls.values())
        if ok:
            logger.info("price_nulls: PASS")
        else:
            logger.error(f"price_nulls: FAIL – {nulls}")
        return ok

    def test_price_non_negative(self, df: pd.DataFrame) -> bool:
        negs = {c: (df[c] < 0).sum() for c in ("price_original","price_sale")}
        ok = all(v == 0 for v in negs.values())
        if ok:
            logger.info("price_non_negative: PASS")
        else:
            logger.error(f"price_non_negative: FAIL – {negs}")
        return ok

    def test_gender_list(self, df: pd.DataFrame) -> bool:
        if "gender" not in df.columns:
            logger.error("gender_list: FAIL – column missing")
            return False
        bad = df[~df["gender"].apply(lambda g: isinstance(g,list))]
        ok = bad.empty
        if ok:
            logger.info("gender_list: PASS")
        else:
            logger.error(f"gender_list: FAIL – {len(bad)} rows not list")
        return ok

    def test_subtitle_and_extra(self, df: pd.DataFrame) -> bool:
        missing = [c for c in ("subTitle","extra") if c not in df.columns]
        ok = not missing
        if ok:
            logger.info("subtitle_and_extra: PASS")
        else:
            logger.error(f"subtitle_and_extra: FAIL – missing {missing}")
        return ok

    def test_extra_valid_json(self, df: pd.DataFrame) -> bool:
        ok = True
        for idx, val in df["extra"].dropna().items():
            try:
                json.loads(val)
            except Exception as e:
                logger.error(f"extra_valid_json: FAIL at row {idx} – {e}")
                ok = False
                break
        if ok:
            logger.info("extra_valid_json: PASS")
        return ok

    def test_duplicate_ids(self, df: pd.DataFrame) -> bool:
        dup = df["id"].duplicated().sum()
        ok = dup == 0
        if ok:
            logger.info("duplicate_ids: PASS")
        else:
            logger.error(f"duplicate_ids: FAIL – {dup} duplicates")
        return ok

    def run(self, df: pd.DataFrame) -> (bool, dict):
        logger.info("Running WorldBalance data-quality tests...")
        results = {
            "price_nulls":         self.test_price_nulls(df),
            "price_non_negative":  self.test_price_non_negative(df),
            "gender_list":         self.test_gender_list(df),
            "subtitle_and_extra":  self.test_subtitle_and_extra(df),
            "extra_valid_json":    self.test_extra_valid_json(df),
            "duplicate_ids":       self.test_duplicate_ids(df),
        }
        overall = all(results.values())
        logger.info(f"OVERALL: {'PASS' if overall else 'FAIL'}")
        return overall, results
