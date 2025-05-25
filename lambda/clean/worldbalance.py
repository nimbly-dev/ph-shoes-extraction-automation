import pandas as pd
from base.base import BaseCleaner

class WorldBalanceCleaner(BaseCleaner):
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        if "id" not in df.columns:
            raise KeyError("DataFrame must contain an 'id' column")

        # cast prices
        df["price_sale"]     = df["price_sale"].astype(int)
        df["price_original"] = df["price_original"].astype(int)

        # normalize gender to lowercase string
        if "gender" in df.columns:
            df["gender"] = df["gender"].apply(
                lambda x: x.lower() if isinstance(x, str) else ""
            )

        # aggregation rules
        agg_dict = {
            "title":          "first",
            "subTitle":       "first",
            "url":            "first",
            "image":          "first",
            "price_sale":     "first",
            "price_original": "first",
            "gender":         self._aggregate_gender,
            "age_group":      "first",
        }

        return df.groupby("id", as_index=False).agg(agg_dict)

    def _aggregate_gender(self, series: pd.Series) -> str:
        vals = {v for v in series if isinstance(v, str) and v}
        if "male" in vals and "female" in vals:
            return "unisex"
        return next(iter(vals), "")
