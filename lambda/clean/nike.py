# clean/nike.py

import json
import pandas as pd
from base.base import BaseCleaner

# strings that usually indicate apparel/accessories (not shoes)
_EXCLUDE_PATTERN = (
    r"(sportswear|tshirt|drifit|t-shirt|cap|shorts|short|"
    r"jacket|hoodie|backpack|socks|trousers|bag)"
)

class NikeCleaner(BaseCleaner):
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        # ensure columns
        for col in ("subTitle", "extra"):
            if col not in df.columns:
                df[col] = None

        # brand
        df["brand"] = "nike"

        # drop rows w/o id
        df = df[df["id"].notna()].copy()

        # prices numeric, non-negative; if original==0 -> set to sale
        for c in ("price_sale","price_original"):
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).clip(lower=0)
        if {"price_sale","price_original"}.issubset(df.columns):
            df.loc[df["price_original"] <= 0, "price_original"] = df["price_sale"]

        # normalize gender to list[str] and compress {male,female} -> ["unisex"]
        if "gender" in df.columns:
            def _norm(g):
                if isinstance(g, list):
                    low = [x.lower() for x in g]
                    return ["unisex"] if set(low) == {"male","female"} else low
                if isinstance(g, str) and g.strip():
                    return [g.lower()]
                return []
            df["gender"] = df["gender"].apply(_norm)

        # filter obvious non-shoes by title/subTitle
        mask1 = ~df["title"].astype(str).str.contains(_EXCLUDE_PATTERN, case=False, na=False)
        mask2 = ~df["subTitle"].astype(str).str.contains(_EXCLUDE_PATTERN, case=False, na=False)
        df = df[mask1 & mask2]

        # normalize/guarantee extra JSON with {"category": str, "sizes": list}
        def _fix_extra(val):
            cat = ""
            sizes = []
            try:
                if isinstance(val, str) and val.strip():
                    obj = json.loads(val)
                    cat = str(obj.get("category","") or "")
                    raw_sizes = obj.get("sizes") or []
                    if isinstance(raw_sizes, list):
                        sizes = [str(s) for s in raw_sizes]
            except Exception:
                pass
            return json.dumps({"category": cat, "sizes": sizes}, ensure_ascii=False)
        df["extra"] = df["extra"].apply(_fix_extra)

        # dedupe
        df = df.drop_duplicates(subset=["id"], keep="first")
        return df.reset_index(drop=True)
