# quality/worldbalance.py

import pandas as pd
import ast
from logger import logger

class WorldBalanceQuality:
    """
    Data-quality tests for WorldBalance cleaned DataFrame.
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

    def test_price_nulls(self, df: pd.DataFrame) -> dict:
        nulls = {
            'price_original': df['price_original'].isnull().sum(),
            'price_sale':     df['price_sale'].isnull().sum()
        }
        if nulls['price_original'] == 0 and nulls['price_sale'] == 0:
            logger.info("Test price_nulls: PASS")
        else:
            logger.error(f"Test price_nulls: FAIL – {nulls}")
        return nulls

    def test_price_non_negative(self, df: pd.DataFrame) -> dict:
        negatives = {
            'price_original': (df['price_original'] < 0).sum(),
            'price_sale':     (df['price_sale'] < 0).sum()
        }
        if negatives['price_original'] == 0 and negatives['price_sale'] == 0:
            logger.info("Test price_non_negative: PASS")
        else:
            logger.error(f"Test price_non_negative: FAIL – {negatives}")
        return negatives

    def test_gender_normalization(self, df: pd.DataFrame) -> int:
        # first coerce any string→list
        df2 = df.copy()
        df2['gender'] = df2['gender'].apply(self._ensure_gender_list)

        # now flag any row where:
        #  1) gender is not a list, OR
        #  2) both 'male' and 'female' appear but not exactly ['unisex']
        invalid = df2[
            df2['gender'].apply(
                lambda x: (not isinstance(x, list)) or
                          ('male' in x and 'female' in x and x != ['unisex'])
            )
        ]
        count = invalid.shape[0]

        if count == 0:
            logger.info("Test gender_normalization: PASS")
        else:
            logger.error(f"Test gender_normalization: FAIL – {count} rows invalid")
        return count

    def test_duplicate_product_ids(self, df: pd.DataFrame) -> int:
        dup_count = df['product_id'].duplicated().sum()
        if dup_count == 0:
            logger.info("Test duplicate_product_ids: PASS")
        else:
            logger.error(f"Test duplicate_product_ids: FAIL – {dup_count} duplicates")
        return dup_count

    def run(self, df: pd.DataFrame) -> (bool, dict):
        logger.info("Running WorldBalance data-quality tests...")
        results = {
            'price_nulls':           self.test_price_nulls(df),
            'negative_prices':       self.test_price_non_negative(df),
            'invalid_gender':        self.test_gender_normalization(df),
            'duplicate_product_ids': self.test_duplicate_product_ids(df),
        }

        overall = (
            results['price_nulls']['price_original'] == 0
            and results['price_nulls']['price_sale'] == 0
            and results['negative_prices']['price_original'] == 0
            and results['negative_prices']['price_sale'] == 0
            and results['invalid_gender'] == 0
            and results['duplicate_product_ids'] == 0
        )

        logger.info(f"OVERALL QUALITY: {'PASS' if overall else 'FAIL'}")
        return overall, results
