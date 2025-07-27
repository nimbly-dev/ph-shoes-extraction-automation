# clean_nike.py

import pandas as pd
from typing import Optional
from dataclasses import dataclass
from base.base import BaseShoe, BaseCleaner

@dataclass
class NikeShoe(BaseShoe):
    colordescription: Optional[str] = None
    out_of_stock:    Optional[bool] = False
    best_seller:     Optional[bool] = False
    brand:           str           = "nike"

class NikeCleaner(BaseCleaner):
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        # 0) Guarantee subTitle & extra exist
        df = self._ensure_columns(df)

        # 1) Fill missing prices with 0
        df["price_sale"]     = df["price_sale"].fillna(0)
        df["price_original"] = df["price_original"].fillna(0)

        # 2) Normalize gender lists
        if "gender" in df.columns:
            def normalize_gender(g):
                if isinstance(g, list):
                    lowered = [x.lower() for x in g]
                    # if both male & female, force unisex
                    if set(lowered) >= {"male", "female"}:
                        return ["unisex"]
                    return lowered
                return []
            df["gender"] = df["gender"].apply(normalize_gender)

        # 3) Clamp negative prices to 0
        df["price_sale"]     = df["price_sale"].clip(lower=0)
        df["price_original"] = df["price_original"].clip(lower=0)

        # 4) Filter out rows where title OR subTitle contains unwanted terms
        pattern = (
            r"(sportswear|tshirt|drifit|t-shirt|cap|shorts|short|"
            r"jacket|hoodie|backpack|socks|trousers|bag)"
        )
        mask_title    = ~df["title"].str.contains(pattern, case=False, na=False)
        mask_subtitle = ~df["subTitle"].fillna("").str.contains(pattern, case=False, na=False)
        df = df[mask_title & mask_subtitle]

        # 5) Set brand explicitly
        df["brand"] = "nike"

        # 6) Drop duplicate IDs
        df = df.drop_duplicates(subset=["id"], keep="first")

        return df

    def _ensure_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Make sure subTitle and extra columns exist so later steps won't KeyError.
        """
        for col in ("subTitle", "extra"):
            if col not in df.columns:
                df[col] = None
        return df
