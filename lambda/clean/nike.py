from typing import Optional
import pandas as pd
from dataclasses import dataclass
from base.base import BaseShoe, BaseCleaner

@dataclass
class NikeShoe(BaseShoe):
    brand:         str = "Nike"
    colordescription: Optional[str] = None
    out_of_stock:    Optional[bool] = False
    best_seller:     Optional[bool] = False

class NikeCleaner(BaseCleaner):
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        1. Fill missing prices with 0.
        2. Lowercase & validate gender.
        3. Clamp negative prices to 0.
        4. Drop duplicate ids.
        """
        # 1) prices
        df["price_sale"]     = df["price_sale"].fillna(0)
        df["price_original"] = df["price_original"].fillna(0)

        # 2) gender → lowercase valid values
        if "gender" in df.columns:
            df["gender"] = (
                df["gender"]
                  .astype(str)
                  .str.lower()
                  .where(df["gender"].isin(["male", "female", "unisex"]), "")
            )

        # 3) clamp negatives
        df["price_sale"]     = df["price_sale"].clip(lower=0)
        df["price_original"] = df["price_original"].clip(lower=0)


        df["brand"]     = "nike"
        # 4) dedupe
        return df.drop_duplicates(subset=["id"], keep="first")
