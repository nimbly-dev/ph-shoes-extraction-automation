import os
import glob
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
    brand: str = ""                     
    year: int = 0
    month: int = 0
    day: int = 0

class FactProductETL:
    """
    Load all CSVs under raw/{year}/{month}/{day}/
    tag brand/year/month/day, dedupe, quality-check.
    """

    def __init__(self,
                 raw_base: str = "raw",
                 year:    Optional[int] = None,
                 month:   Optional[int] = None,
                 day:     Optional[int] = None):
        # default to today if not provided
        today = datetime.utcnow()
        self.year  = year  if year  is not None else today.year
        self.month = month if month is not None else today.month
        self.day   = day   if day   is not None else today.day

        # build the glob pattern under raw_base
        # e.g. raw/2025/05/04/*.csv
        path = os.path.join(
            raw_base,
            f"{self.year}",
            f"{self.month:02d}",
            f"{self.day:02d}"
        )
        self.pattern = os.path.join(path, "*.csv")
        logger.info(f"ETL will read from: {self.pattern}")

        # determine which columns belong to our dataclass
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
            brand = os.path.basename(fn).split("_")[0]
            df = pd.read_csv(fn)
            df["brand"]  = brand
            df["year"]   = self.year
            df["month"]  = self.month
            df["day"]    = self.day
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