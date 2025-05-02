from typing import Optional

import pandas as pd

from base.base import BaseShoe, BaseCleaner
from logger import logger
from dataclasses import dataclass


@dataclass
class NikeShoe(BaseShoe):
    colordescription: Optional[str] = None
    out_of_stock:    Optional[bool] = False
    best_seller:     Optional[bool] = False

class NikeCleaner(BaseCleaner):
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and transform the Nike DataFrame:
          1. Fill nulls in price_sale & price_original with 0.
          2. Normalize gender lists: ['male','female'] → ['unisex'].
          3. Clamp negative prices to 0.
          4. Drop duplicate id’s, keeping first.
        """
        df['price_sale']     = df['price_sale'].fillna(0)
        df['price_original'] = df['price_original'].fillna(0)

        def _normalize_gender(genders):
            if isinstance(genders, list) and 'male' in genders and 'female' in genders:
                return ['unisex']
            return genders

        if 'gender' in df.columns:
            df['gender'] = df['gender'].apply(_normalize_gender)

        df['price_sale']     = df['price_sale'].apply(lambda x: x if x >= 0 else 0)
        df['price_original'] = df['price_original'].apply(lambda x: x if x >= 0 else 0)

        df = df.drop_duplicates(subset=['id'], keep='first')

        return df
