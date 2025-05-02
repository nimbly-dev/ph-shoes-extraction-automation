import pandas as pd
from typing import List, Optional
from dataclasses import dataclass

from base.base import BaseShoe, BaseCleaner

@dataclass
class WorldBalanceShoe(BaseShoe):
    pass

class WorldBalanceCleaner(BaseCleaner):
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df['price_original'] = df['price_original'].astype(int)
        df['price_sale']     = df['price_sale'].astype(int)

        if 'gender' in df.columns:
            df['gender'] = df['gender'].apply(self._normalize_gender)

        agg_dict = {
            'product_name':   'first',
            'price_original': 'first',
            'price_sale':     'first',
            'url':            'first',
            'image':          'first',
            'gender':         self._aggregate_genders,
            'age_group':      'first',
            'subtitle':       'first',
            'color_variants': self._aggregate_colors
        }

        return df.groupby('product_id', as_index=False).agg(agg_dict)

    def _normalize_gender(self, gender):
        if isinstance(gender, list):
            return [g.lower() for g in gender]
        if isinstance(gender, str):
            return [gender.lower()]
        return []

    def _aggregate_genders(self, series):
        s = set(g for lst in series for g in lst)
        if 'male' in s and 'female' in s:
            return ['unisex']
        return sorted(s)

    def _aggregate_colors(self, series):
        return sorted({c for lst in series if isinstance(lst, list) for c in lst})