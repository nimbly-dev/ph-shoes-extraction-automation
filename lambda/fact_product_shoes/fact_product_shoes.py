import os
import glob
import re
import time
import pandas as pd
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List
from uuid import uuid4

from base.base import BaseShoe
from logger import logger  

@dataclass
class FactProductShoe(BaseShoe):
    brand: str
    year: int
    month: int
    day: int

class FactProductETL:
    """
    Load all CSVs under fact_product_shoes/year=…/month=…/day=…/,
    parse partitions for year/month/day, tag brand, dedupe, quality-check.
    """

    def __init__(self, base_path: str = "fact_product_shoes"):
        self.base_path = base_path
        self.pattern = os.path.join(base_path, "year=*","month=*","day=*","*.csv")
        self.fact_fields = list(FactProductShoe.__dataclass_fields__.keys())

    def load_fact_products(self) -> pd.DataFrame:
        files = glob.glob(self.pattern)
        if not files:
            logger.error(f"No files found matching {self.pattern}")
            raise FileNotFoundError(f"No files found matching {self.pattern}")

        logger.info("Found files:")
        for f in files:
            logger.info(f"  {f}")

        start = time.time()
        parts = []
        for fn in files:
            m = re.search(r"year=(\d+)/month=(\d+)/day=(\d+)", fn)
            if not m:
                logger.error(f"Could not parse partition from path {fn}")
                raise ValueError(f"Could not parse partition from path {fn}")
            yr, mo, dy = map(int, m.groups())

            brand = os.path.basename(fn).split("_")[0]

            df = pd.read_csv(fn)
            df["brand"] = brand
            df["year"]  = yr
            df["month"] = mo
            df["day"]   = dy
            parts.append(df)

        df_all = pd.concat(parts, ignore_index=True)
        df_fact = df_all[self.fact_fields].drop_duplicates().reset_index(drop=True)

        self._quality_checks(df_fact)

        elapsed = time.time() - start
        logger.info(f"Loaded {len(df_fact)} rows in {elapsed:.3f}s")
        return df_fact

    def _quality_checks(self, df: pd.DataFrame):
        errs = []

        dups = df.duplicated(subset=["brand","id"]).sum()
        if dups:
            errs.append(f"{dups} duplicate (brand,id) rows")

        full_nan = [c for c in df.columns if df[c].isna().all()]
        if full_nan:
            errs.append(f"columns all-NaN: {full_nan}")

        missing_sale = df["price_sale"].isna().sum()
        if missing_sale:
            errs.append(f"{missing_sale} rows missing price_sale")

        missing_id = df["id"].isna().sum()
        missing_brand = df["brand"].isna().sum()
        if missing_id:
            errs.append(f"{missing_id} rows missing id")
        if missing_brand:
            errs.append(f"{missing_brand} rows missing brand")

        if errs:
            msg = "Data quality check failed:\n  - " + "\n  - ".join(errs)
            logger.error(msg)
            raise ValueError(msg)
