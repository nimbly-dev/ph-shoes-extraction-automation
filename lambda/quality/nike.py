# quality/nike.py

import pandas as pd
import ast
from logger import logger

class NikeQuality:
    """
    Run data-quality tests on a Nike DataFrame.
    """

    def _ensure_gender_list(self, g):
        """
        If g is a string that looks like a Python list, literal_eval it.
        Otherwise, wrap scalars into [g], leave lists as-is, or [] for null.
        """
        if isinstance(g, str):
            try:
                val = ast.literal_eval(g)
                if isinstance(val, list):
                    return val
            except (ValueError, SyntaxError):
                pass
            return [g]
        if isinstance(g, list):
            return g
        if pd.notnull(g):
            return [g]
        return []

    def test_no_nulls(self, df: pd.DataFrame) -> bool:
        cols = ['price_sale', 'price_original']
        ok = True
        for c in cols:
            n = df[c].isnull().sum()
            if n:
                logger.error(f"Test Failed: {c} has {n} null(s).")
                ok = False
            else:
                logger.debug(f"Test Passed: {c} has no nulls.")
        return ok

    def test_gender_normalization(self, df: pd.DataFrame) -> bool:
        ok = True
        df2 = df.copy()
        df2['gender'] = df2['gender'].apply(self._ensure_gender_list)

        for _, row in df2.iterrows():
            g = row['gender']
            if 'male' in g and 'female' in g:
                if g != ['unisex']:
                    logger.error(f"Test Failed: id={row['id']} should be ['unisex'] but is {g}.")
                    ok = False
                else:
                    logger.debug(f"Test Passed: id={row['id']} normalized to ['unisex'].")
            elif not isinstance(g, list):
                logger.error(f"Test Failed: id={row['id']} gender not list ({g!r}).")
                ok = False
            else:
                logger.debug(f"Test Passed: id={row['id']} gender={g}.")
        return ok

    def test_numeric_fields(self, df: pd.DataFrame) -> bool:
        ok = True
        for _, row in df.iterrows():
            for c in ['price_sale', 'price_original']:
                if row[c] < 0:
                    logger.error(f"Test Failed: id={row['id']} has negative {c}: {row[c]}")
                    ok = False
                else:
                    logger.debug(f"Test Passed: id={row['id']} {c}={row[c]}")
        return ok

    def run(self, df: pd.DataFrame) -> (bool, dict):
        logger.info("Running Nike data-quality tests...")
        r1 = self.test_no_nulls(df)
        r2 = self.test_gender_normalization(df)
        r3 = self.test_numeric_fields(df)

        overall = r1 and r2 and r3
        results = {
            'no_nulls':    r1,
            'gender_norm': r2,
            'numeric':     r3,
        }

        logger.info(f"No‐nulls: {'PASS' if r1 else 'FAIL'}")
        logger.info(f"Gender-norm: {'PASS' if r2 else 'FAIL'}")
        logger.info(f"Numeric: {'PASS' if r3 else 'FAIL'}")
        logger.info(f"OVERALL: {'PASS' if overall else 'FAIL'}")

        return overall, results
