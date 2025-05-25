import pandas as pd
from logger import logger
from clean.hoka import HokaCleaner

class HokaQuality:
    """
    Data-quality tests for Hoka cleaned DataFrame.
    """

    def __init__(self):
        self.cleaner = HokaCleaner()

    def test_add_brand(self, df: pd.DataFrame) -> bool:
        df2 = self.cleaner._add_brand(df.copy())
        return (df2["brand"] == "hoka").all()

    def test_set_nulls_to_none(self, df: pd.DataFrame) -> bool:
        df2 = df.copy()
        col = next(c for c in df2.columns if c != "id")
        if df2[col].notnull().all():
            df2.at[df2.index[0], col] = pd.NA
        out = self.cleaner._set_nulls_to_none(df2)
        return out.at[df2.index[0], col] is None

    def test_filter_missing_id(self, df: pd.DataFrame) -> bool:
        df2 = df.copy()
        if df2["id"].notnull().all():
            df2.at[df2.index[0], "id"] = pd.NA
        out = self.cleaner._filter_missing_id(df2)
        return out["id"].notnull().all()

    def test_update_gender_based_on_title(self, df: pd.DataFrame) -> bool:
        df2 = df.copy()
        if {"age_group", "title", "gender"}.issubset(df2.columns):
            idxs = df2.index[df2["age_group"] == "adult"].tolist() or [df2.index[0]]
            idx = idxs[0]
            df2.at[idx, "title"]  = f"{df2.at[idx,'title']} Unisex"
            df2.at[idx, "gender"] = "male"
            out = self.cleaner._update_gender_based_on_title(df2)
            return out.at[idx, "gender"] == "unisex"
        return True

    def test_remove_duplicates(self, df: pd.DataFrame) -> bool:
        out = self.cleaner._remove_duplicates(df.copy())
        return out["id"].nunique() == len(out)

    def test_convert_price_columns(self, df: pd.DataFrame) -> bool:
        df2 = df.copy()
        for col in ["price_sale", "price_original"]:
            if col in df2:
                df2[col] = df2[col].astype(object)
                df2.at[df2.index[0], col] = "₱1,234"
        out = self.cleaner._convert_price_columns(df2)
        return all(
            pd.api.types.is_numeric_dtype(out[c])
            for c in ["price_sale", "price_original"]
            if c in out
        )

    def test_clean_title(self, df: pd.DataFrame) -> bool:
        df2 = df.copy()
        if "title" in df2:
            df2.at[df2.index[0], "title"] = "Men's X Women's Y Kid's Z"
            out = self.cleaner._clean_title(df2)
            return out.at[df2.index[0], "title"] == "X Y Z"
        return True

    def run(self, df: pd.DataFrame) -> (bool, dict):
        logger.info("Running Hoka data-quality tests...")
        results = {
            "add_brand":                    self.test_add_brand(df),
            "set_nulls_to_none":            self.test_set_nulls_to_none(df),
            "filter_missing_id":            self.test_filter_missing_id(df),
            "update_gender_based_on_title": self.test_update_gender_based_on_title(df),
            "remove_duplicates":            self.test_remove_duplicates(df),
            "convert_price_columns":        self.test_convert_price_columns(df),
            "clean_title":                  self.test_clean_title(df),
        }
        overall = all(results.values())
        for name, ok in results.items():
            logger.info(f"{name}: {'PASS' if ok else 'FAIL'}")
        logger.info(f"OVERALL: {'PASS' if overall else 'FAIL'}")
        return overall, results
