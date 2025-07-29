# clean/nike.py

import pandas as pd
from base.base import BaseCleaner


class NikeCleaner(BaseCleaner):
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        # 0) Ensure subTitle & extra exist
        for col in ("subTitle", "extra"):
            if col not in df.columns:
                df[col] = None

        # 1) Fill missing prices with 0
        df["price_sale"]     = df["price_sale"].fillna(0)
        df["price_original"] = df["price_original"].fillna(0)

        # 2) Normalize gender lists
        if "gender" in df.columns:
            def normalize_gender(g):
                if isinstance(g, list):
                    low = [x.lower() for x in g]
                    if {"male","female"}.issubset(set(low)):
                        return ["unisex"]
                    return low
                return []
            df["gender"] = df["gender"].apply(normalize_gender)

        # 3) Clamp negative prices
        df["price_sale"]     = df["price_sale"].clip(lower=0)
        df["price_original"] = df["price_original"].clip(lower=0)

        # 4) Filter unwanted titles/subtitles
        pattern = (
            r"(sportswear|tshirt|drifit|t-shirt|cap|shorts|short|"
            r"jacket|hoodie|backpack|socks|trousers|bag)"
        )
        mask1 = ~df["title"].str.contains(pattern, case=False, na=False)
        mask2 = ~df["subTitle"].fillna("").str.contains(pattern, case=False, na=False)
        df = df[mask1 & mask2]

        # 5) Set brand explicitly
        df["brand"] = "nike"

        # 6) Drop duplicate IDs
        df = df.drop_duplicates(subset=["id"], keep="first")

        return df
