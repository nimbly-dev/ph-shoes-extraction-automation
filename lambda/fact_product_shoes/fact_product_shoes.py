import os
import re
import time
import pandas as pd
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List
from uuid import uuid4
import boto3

from base.base import BaseShoe
from logger import logger  

@dataclass
class FactProductShoe(BaseShoe):
    brand: str = ""
    dwid: str = ""
    year: int = 0
    month: int = 0
    day: int = 0

class FactProductETL:
    """
    Loads CSVs from S3 under raw/{year}/{month}/{day}/,
    tags each row with brand/year/month/day,
    dedupes, runs quality checks, and returns a DataFrame.
    """

    def __init__(self,
                 bucket:    Optional[str] = None,
                 raw_prefix:str       = "raw",
                 year:      Optional[int]  = None,
                 month:     Optional[int]  = None,
                 day:       Optional[int]  = None):
        # S3 client
        self.s3     = boto3.client("s3")
        self.bucket = bucket or os.environ["S3_BUCKET"]

        # partitions default to today
        today = datetime.utcnow()
        self.dwid = f"{year or today.year}{month or today.month:02d}{day or today.day:02d}"
        self.year  = year  or today.year
        self.month = month or today.month
        self.day   = day   or today.day

        # S3 prefix under which CSVs live
        self.prefix = f"{raw_prefix}/{self.year}/{self.month:02d}/{self.day:02d}/"
        logger.info(f"ETL will read from s3://{self.bucket}/{self.prefix}")

        # columns to keep in fact
        self.fact_fields = list(FactProductShoe.__dataclass_fields__.keys())

    def load_fact_products(self) -> pd.DataFrame:
        # … all the listing & reading code stays exactly the same …
        parts = []
        for key in keys:
            # … read CSV into df, add brand/year/month/day/dwid …
            df["brand"] = brand
            df["year"]  = self.year
            df["month"] = self.month
            df["day"]   = self.day
            df["dwid"]  = self.dwid
            parts.append(df)

        df_all = pd.concat(parts, ignore_index=True)

        # define the “fixed” front‐of‐table order:
        front = ["dwid","year","month","day","brand"]
        # then all the other columns in whatever order they appeared
        others = [c for c in df_all.columns if c not in front]
        desired_order = front + others

        # now select in that exact order, drop dups, reset index
        df_fact = df_all[desired_order].drop_duplicates().reset_index(drop=True)

        self._quality_checks(df_fact)
        return df_fact

    def _quality_checks(self, df: pd.DataFrame):
        errs = []
        dups = df.duplicated(subset=["brand","id"]).sum()
        if dups: errs.append(f"{dups} duplicate (brand,id) rows")

        full_nan = [c for c in df.columns if df[c].isna().all()]
        if full_nan: errs.append(f"columns all-NaN: {full_nan}")

        missing_sale = df["price_sale"].isna().sum()
        if missing_sale: errs.append(f"{missing_sale} rows missing price_sale")

        missing_id    = df["id"].isna().sum()
        missing_brand = df["brand"].isna().sum()
        if missing_id:    errs.append(f"{missing_id} rows missing id")
        if missing_brand: errs.append(f"{missing_brand} rows missing brand")

        if errs:
            msg = "Data quality check failed:\n  - " + "\n  - ".join(errs)
            logger.error(msg)
            raise ValueError(msg)