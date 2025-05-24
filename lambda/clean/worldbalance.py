import pandas as pd
from typing import List
from base.base import BaseCleaner

class WorldBalanceCleaner(BaseCleaner):
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        # Ensure our primary key matches BaseShoe.id
        if 'id' not in df.columns:
            raise KeyError("DataFrame must contain an 'id' column for grouping")

        # Cast prices to integers
        df['price_sale']     = df['price_sale'].astype(int)
        df['price_original'] = df['price_original'].astype(int)

        # Normalize gender values into lowercase lists
        if 'gender' in df.columns:
            df['gender'] = df['gender'].apply(self._normalize_gender)

        # Define aggregation rules in terms of BaseShoe fields
        agg_dict = {
            'title':          'first',
            'subTitle':       'first',
            'url':            'first',
            'image':          'first',
            'price_sale':     'first',
            'price_original': 'first',
            'gender':         self._aggregate_genders,
            'age_group':      'first',
        }

        # Group by the shoe 'id' and apply aggregations
        return df.groupby('id', as_index=False).agg(agg_dict)

    def _normalize_gender(self, gender) -> List[str]:
        if isinstance(gender, list):
            return [g.lower() for g in gender if isinstance(g, str)]
        if isinstance(gender, str):
            return [gender.lower()]
        return []

    def _aggregate_genders(self, series) -> List[str]:
        genders = {g for lst in series if isinstance(lst, list) for g in lst}
        if 'male' in genders and 'female' in genders:
            return ['unisex']
        return sorted(genders)
