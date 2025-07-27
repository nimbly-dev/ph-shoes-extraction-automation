# clean/world_balance.py

import pandas as pd
from typing import List
from base.base import BaseCleaner

class WorldBalanceCleaner(BaseCleaner):
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        # 0) Ensure subTitle & extra columns exist
        for col in ("subTitle", "extra"):
            if col not in df.columns:
                df[col] = None

        if "id" not in df.columns:
            raise KeyError("DataFrame must contain an 'id' column")

        # 1) Prices → numeric & non-negative
        df["price_sale"]     = pd.to_numeric(df["price_sale"], errors="coerce").fillna(0).clip(lower=0)
        df["price_original"] = pd.to_numeric(df["price_original"], errors="coerce").fillna(0).clip(lower=0)

        # 2) Normalize gender to a list
        if "gender" in df.columns:
            df["gender"] = df["gender"].apply(
                lambda g: [g.lower()] if isinstance(g, str) and g else []
            )

        # 3) Set brand
        df["brand"] = "worldbalance"

        # 4) Aggregate duplicates by `id`
        def agg_gender(series: pd.Series) -> List[str]:
            # series is a column of lists; flatten & dedupe
            all_genders = set(sum(series.tolist(), []))
            if {"male", "female"}.issubset(all_genders):
                return ["unisex"]
            return sorted(all_genders)

        agg_dict = {
            "title":           "first",
            "subTitle":        "first",
            "url":             "first",
            "image":           "first",
            "price_sale":      "first",
            "price_original":  "first",
            "gender":          agg_gender,
            "age_group":       "first",
            "brand":           "first",
            "extra":           "first",
        }

        return df.groupby("id", as_index=False).agg(agg_dict)
