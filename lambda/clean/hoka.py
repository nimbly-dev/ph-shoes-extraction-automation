# clean/hoka.py

import pandas as pd
from dataclasses import dataclass
from base.base import BaseShoe, BaseCleaner

@dataclass
class HokaShoe(BaseShoe):
    """
    A simple subclass of BaseShoe for typing clarity.
    """
    pass


class HokaCleaner(BaseCleaner):
    """
    Cleans a DataFrame of raw Hoka shoe records, ensuring:
      - All canonical columns exist (including subTitle & extra)
      - Nulls are converted to None
      - Missing IDs are dropped
      - Gender is corrected based on title for adult unisex
      - Duplicates are removed
      - Price columns are numeric
      - Titles are tidied
      - Missing images are filled
    """

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        # 0) Ensure subTitle & extra columns exist
        df = self._ensure_columns(df)

        # 1) Add brand column
        df = self._add_brand(df)

        # 2) Convert pandas nulls to Python None (except id)
        df = self._set_nulls_to_none(df)

        # 3) Drop any rows missing an id
        df = self._filter_missing_id(df)

        # 4) Normalize gender for adult unisex cases
        df = self._update_gender_based_on_title(df)

        # 5) Remove duplicate ids
        df = self._remove_duplicates(df)

        # 6) Convert price strings → numeric
        df = self._convert_price_columns(df)

        # 7) Clean up title text
        df = self._clean_title(df)

        # 8) Fill missing images
        df = self._fill_missing_image(df)

        return df

    def _ensure_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Guarantee that 'subTitle' and 'extra' exist,
        so downstream code never KeyErrors.
        """
        for col in ["subTitle", "extra"]:
            if col not in df.columns:
                df[col] = None
        return df

    def _add_brand(self, df: pd.DataFrame) -> pd.DataFrame:
        df["brand"] = "hoka"
        return df

    def _set_nulls_to_none(self, df: pd.DataFrame) -> pd.DataFrame:
        # Turn any pandas NA/NaN into Python None for all columns except 'id'
        for col in df.columns:
            if col != "id":
                df[col] = df[col].where(df[col].notna(), None)
        return df

    def _filter_missing_id(self, df: pd.DataFrame) -> pd.DataFrame:
        # Drop rows where 'id' is null or None
        return df[df["id"].notna()].copy()

    def _update_gender_based_on_title(self, df: pd.DataFrame) -> pd.DataFrame:
        # If age_group is 'adult' and title contains 'unisex', force gender to 'unisex'
        if {"gender", "age_group", "title"}.issubset(df.columns):
            def fix_gender(row):
                if row["age_group"] == "adult" and isinstance(row["title"], str):
                    if "unisex" in row["title"].lower():
                        return "unisex"
                return row["gender"]
            df["gender"] = df.apply(fix_gender, axis=1)
        return df

    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        # Keep only the first occurrence of each id
        return df.drop_duplicates(subset=["id"], keep="first")

    def _convert_price_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        # Convert price columns to numeric, coerce errors to NaN (later None)
        for col in ["price_sale", "price_original"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    def _clean_title(self, df: pd.DataFrame) -> pd.DataFrame:
        # Remove "Men's", "Women's", "Kid's" and extra whitespace
        if "title" in df.columns:
            df["title"] = (
                df["title"]
                  .str.replace(r"(?i)men's|women's|kid's", "", regex=True)
                  .str.replace(r"\s+", " ", regex=True)
                  .str.strip()
            )
        return df

    def _fill_missing_image(self, df: pd.DataFrame) -> pd.DataFrame:
        # Replace missing images with a placeholder
        if "image" in df.columns:
            df["image"] = df["image"].fillna("no_image.png")
        return df
