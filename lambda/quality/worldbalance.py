import pandas as pd
from logger import logger

class WorldBalanceQuality:
    """
    Data-quality tests for WorldBalance cleaned DataFrame.
    """

    def test_price_nulls(self, df: pd.DataFrame) -> dict:
        nulls = {
            "price_original": df["price_original"].isnull().sum(),
            "price_sale":     df["price_sale"].isnull().sum(),
        }
        if all(v == 0 for v in nulls.values()):
            logger.info("Test price_nulls: PASS")
        else:
            logger.error(f"Test price_nulls: FAIL – {nulls}")
        return nulls

    def test_price_non_negative(self, df: pd.DataFrame) -> dict:
        negs = {
            "price_original": (df["price_original"] < 0).sum(),
            "price_sale":     (df["price_sale"] < 0).sum(),
        }
        if all(v == 0 for v in negs.values()):
            logger.info("Test price_non_negative: PASS")
        else:
            logger.error(f"Test price_non_negative: FAIL – {negs}")
        return negs

    def test_gender_values(self, df: pd.DataFrame) -> int:
        invalid = df[~df["gender"].isin(["male", "female", "unisex", ""])]
        count = invalid.shape[0]
        if count == 0:
            logger.info("Test gender_values: PASS")
        else:
            logger.error(f"Test gender_values: FAIL – {count} invalid rows")
        return count

    def test_duplicate_ids(self, df: pd.DataFrame) -> int:
        if "id" not in df.columns:
            logger.error("Test duplicate_ids: FAIL – 'id' column missing")
            return -1
        dup_count = df["id"].duplicated().sum()
        if dup_count == 0:
            logger.info("Test duplicate_ids: PASS")
        else:
            logger.error(f"Test duplicate_ids: FAIL – {dup_count} duplicates")
        return dup_count

    def run(self, df: pd.DataFrame) -> (bool, dict):
        logger.info("Running WorldBalance data-quality tests...")
        r1 = self.test_price_nulls(df)
        r2 = self.test_price_non_negative(df)
        r3 = self.test_gender_values(df)
        r4 = self.test_duplicate_ids(df)

        overall = (
            r1["price_original"] == 0 and
            r1["price_sale"]     == 0 and
            r2["price_original"] == 0 and
            r2["price_sale"]     == 0 and
            r3 == 0 and
            r4 == 0
        )
        logger.info(f"OVERALL: {'PASS' if overall else 'FAIL'}")
        return overall, {
            "price_nulls":       r1,
            "price_non_negative":r2,
            "gender_values":     r3,
            "duplicate_ids":     r4,
        }
