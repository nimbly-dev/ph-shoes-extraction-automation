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
        # list CSV objects under that prefix
        paginator = self.s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.bucket, Prefix=self.prefix)
        keys = []
        for page in pages:
            for obj in page.get("Contents", []):
                if obj["Key"].lower().endswith(".csv"):
                    keys.append(obj["Key"])

        if not keys:
            logger.error(f"No CSVs found under s3://{self.bucket}/{self.prefix}")
            raise FileNotFoundError(f"No CSVs under {self.prefix}")

        logger.info(f"Found {len(keys)} files to load")
        start = time.time()
        parts = []
        for key in keys:
            brand = os.path.basename(key).split("_")[0]
            logger.info(f"Reading s3://{self.bucket}/{key}")
            resp = self.s3.get_object(Bucket=self.bucket, Key=key)
            df = pd.read_csv(resp["Body"])
            df["brand"]  = brand
            df["year"]   = self.year
            df["month"]  = self.month
            df["day"]    = self.day
            parts.append(df)

        df_all  = pd.concat(parts, ignore_index=True)
        df_fact = df_all[self.fact_fields].drop_duplicates().reset_index(drop=True)

        self._quality_checks(df_fact)

        elapsed = time.time() - start
        logger.info(f"Loaded {len(df_fact)} rows in {elapsed:.3f}s")
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