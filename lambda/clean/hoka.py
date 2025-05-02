# clean/hoka.py

import pandas as pd
from typing import List, Optional
from dataclasses import dataclass
from base.base import BaseShoe, BaseCleaner

@dataclass
class HokaShoe(BaseShoe):
    pass

class HokaCleaner(BaseCleaner):
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self._add_brand(df)
        df = self._set_nulls_to_none(df)
        df = self._filter_missing_id(df)
        df = self._update_gender_based_on_title(df)
        df = self._remove_duplicates(df)
        df = self._convert_price_columns(df)
        df = self._clean_title(df)
        return df

    def _add_brand(self, df: pd.DataFrame) -> pd.DataFrame:
        df["brand"] = "hoka"
        return df

    def _set_nulls_to_none(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in df.columns:
            if col != "id":
                df[col] = df[col].apply(lambda x: None if pd.isna(x) else x)
        return df

    def _filter_missing_id(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[df["id"].notnull()].copy()

    def _update_gender_based_on_title(self, df: pd.DataFrame) -> pd.DataFrame:
        def fix_gender(row):
            if row.get("age_group") == "adult" and row.get("title"):
                if "unisex" in row["title"].lower():
                    return ["unisex"]
            return row.get("gender")
        if {"gender","age_group","title"}.issubset(df.columns):
            df["gender"] = df.apply(fix_gender, axis=1)
        return df

    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.drop_duplicates(subset=["id"], keep="first")

    def _convert_price_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in ["price_sale","price_original"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    def _clean_title(self, df: pd.DataFrame) -> pd.DataFrame:
        if "title" in df.columns:
            df["title"] = (
                df["title"]
                .str.replace(r"(?i)men's|women's|kid's", "", regex=True)
                .str.replace(r"\s+", " ", regex=True)
                .str.strip()
            )
        return df
