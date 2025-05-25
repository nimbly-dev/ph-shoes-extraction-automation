import pandas as pd
from logger import logger

class NikeQuality:
    """
    Data-quality tests for Nike cleaned DataFrame.
    """

    def test_no_nulls(self, df: pd.DataFrame) -> bool:
        ok = True
        for c in ["price_sale", "price_original"]:
            n = df[c].isnull().sum()
            if n:
                logger.error(f"Test Failed: {c} has {n} null(s).")
                ok = False
            else:
                logger.debug(f"Test Passed: {c} has no nulls.")
        return ok

    def test_gender_values(self, df: pd.DataFrame) -> bool:
        ok = True
        for _, row in df.iterrows():
            g = row.get("gender", "")
            if g not in ("male", "female", "unisex", ""):
                logger.error(f"Test Failed: id={row['id']} invalid gender: {g!r}")
                ok = False
            else:
                logger.debug(f"Test Passed: id={row['id']} gender={g!r}")
        return ok

    def test_numeric_fields(self, df: pd.DataFrame) -> bool:
        ok = True
        for _, row in df.iterrows():
            for c in ["price_sale", "price_original"]:
                if row[c] < 0:
                    logger.error(f"Test Failed: id={row['id']} negative {c}: {row[c]}")
                    ok = False
                else:
                    logger.debug(f"Test Passed: id={row['id']} {c}={row[c]}")
        return ok

    def run(self, df: pd.DataFrame) -> (bool, dict):
        logger.info("Running Nike data-quality tests...")
        r1 = self.test_no_nulls(df)
        r2 = self.test_gender_values(df)
        r3 = self.test_numeric_fields(df)
        overall = r1 and r2 and r3

        results = {
            "no_nulls":     r1,
            "gender_values":r2,
            "numeric":      r3,
        }
        logger.info(f"No‐nulls: {'PASS' if r1 else 'FAIL'}")
        logger.info(f"Gender-values: {'PASS' if r2 else 'FAIL'}")
        logger.info(f"Numeric: {'PASS' if r3 else 'FAIL'}")
        logger.info(f"OVERALL: {'PASS' if overall else 'FAIL'}")
        return overall, results
