# clean/hoka.py

import pandas as pd
import json
from dataclasses import dataclass
from base.base import BaseShoe, BaseCleaner

SIZE_SET = {
    "6","6.5","7","7.5","8","8.5","9","9.5","10","10.5","11","11.5","12","13"
}

@dataclass
class HokaShoe(BaseShoe):
    pass


class HokaCleaner(BaseCleaner):
    """
    - Ensure subTitle & extra exist
    - Brand = hoka
    - Drop rows without id
    - Convert prices to numeric; if price_original=0, set to price_sale
    - Strip gendered prefixes from title (Men's/Women's/Kid's)
    - Normalize gender to a list[str]
    - De-dupe by id
    - Fill missing image
    - Normalize extra: JSON with {"category": <str>, "sizes": [<6..13>]}
    """

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self._ensure_columns(df)
        df = self._add_brand(df)
        df = self._filter_missing_id(df)
        df = self._convert_price_columns(df)
        df = self._clean_title(df)
        df = self._normalize_gender(df)
        df = self._normalize_extra(df)
        df = self._fill_missing_image(df)
        df = df.drop_duplicates(subset=["id"], keep="first")
        return df.reset_index(drop=True)

    def _ensure_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in ["subTitle", "extra"]:
            if col not in df.columns:
                df[col] = None
        return df

    def _add_brand(self, df: pd.DataFrame) -> pd.DataFrame:
        df["brand"] = "hoka"
        return df

    def _filter_missing_id(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[df["id"].notna()].copy()

    def _convert_price_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in ["price_sale", "price_original"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        # if original is zero, mirror sale
        if {"price_sale","price_original"}.issubset(df.columns):
            df.loc[df["price_original"] <= 0, "price_original"] = df["price_sale"]
        return df

    def _clean_title(self, df: pd.DataFrame) -> pd.DataFrame:
        if "title" in df.columns:
            df["title"] = (
                df["title"].astype(str)
                .str.replace(r"(?i)^\s*(men's|women's|kids?|kid's)\s+", "", regex=True)
                .str.replace(r"\s+", " ", regex=True)
                .str.strip()
            )
        return df

    def _normalize_gender(self, df: pd.DataFrame) -> pd.DataFrame:
        if "gender" in df.columns:
            def _norm(g):
                if isinstance(g, list):
                    return [x.lower() for x in g]
                if isinstance(g, str) and g.strip():
                    return [g.lower()]
                return []
            df["gender"] = df["gender"].apply(_norm)
        return df

    def _normalize_extra(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Force `extra` to be a JSON string with {'category': str, 'sizes': [6..13]}.
        If an 'extra' exists already, merge/clean it; else create empty.
        """
        def _fix(val):
            cat = ""
            sizes = []
            try:
                if isinstance(val, str) and val.strip():
                    obj = json.loads(val)
                    cat = str(obj.get("category", "")).strip()
                    raw_sizes = obj.get("sizes") or []
                    if isinstance(raw_sizes, list):
                        sizes = [s for s in map(str, raw_sizes) if s in SIZE_SET]
            except Exception:
                pass
            return json.dumps({"category": cat, "sizes": sizes}, ensure_ascii=False)
        df["extra"] = df["extra"].apply(_fix)
        return df

    def _fill_missing_image(self, df: pd.DataFrame) -> pd.DataFrame:
        if "image" in df.columns:
            df["image"] = df["image"].fillna("no_image.png")
        return df
