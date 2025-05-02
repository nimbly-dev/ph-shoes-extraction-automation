# quality/worldbalance.py

import pandas as pd
from logger import logger

class WorldBalanceQuality:
    """
    Data‑quality tests for WorldBalance cleaned DataFrame.
    """

    def test_price_nulls(self, df: pd.DataFrame) -> dict:
        """Test that 'price_original' and 'price_sale' have no null values."""
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
        """Test that all 'price_original' and 'price_sale' values are non-negative."""
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
        """
        Test that if both 'male' and 'female' appear in a row's gender,
        the normalized value is exactly ['unisex'].
        """
        invalid = df[
            df['gender'].apply(lambda x: isinstance(x, list) and 'male' in x and 'female' in x and x != ['unisex'])
        ]
        count = invalid.shape[0]
        if count == 0:
            logger.info("Test gender_normalization: PASS")
        else:
            logger.error(f"Test gender_normalization: FAIL – {count} rows invalid")
        return count

    def test_duplicate_product_ids(self, df: pd.DataFrame) -> int:
        """Test that there are no duplicate product_id values."""
        dup_count = df['product_id'].duplicated().sum()
        if dup_count == 0:
            logger.info("Test duplicate_product_ids: PASS")
        else:
            logger.error(f"Test duplicate_product_ids: FAIL – {dup_count} duplicates")
        return dup_count

    def run(self, df: pd.DataFrame) -> (bool, dict):
        """
        Run all tests. Returns (overall_passed, results_dict).
        results_dict keys:
          - price_nulls: dict
          - negative_prices: dict
          - invalid_gender: int
          - duplicate_product_ids: int
        """
        logger.info("Running WorldBalance data-quality tests...")
        results = {
            'price_nulls':           self.test_price_nulls(df),
            'negative_prices':       self.test_price_non_negative(df),
            'invalid_gender':        self.test_gender_normalization(df),
            'duplicate_product_ids': self.test_duplicate_product_ids(df),
        }

        # overall pass if no nulls, no negatives, no invalid genders, no duplicates
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
