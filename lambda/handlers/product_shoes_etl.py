# handlers/product_shoes_etl.py

import os
import json
import logging
from datetime import datetime

from fact_product_shoes.fact_product_shoes import FactProductETL  
from utils.parquet_util import ParquetUtil

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("FactProductETL Lambda started…")

    # read optional year/month/day from query params (or fall back to ETL defaults)
    params = event.get("queryStringParameters") or {}
    yr = int(params.get("year",  0)) or None
    mo = int(params.get("month", 0)) or None
    dy = int(params.get("day",   0)) or None

    try:
        # instantiate ETL (it will default to today if any of yr,mo,dy is None)
        etl = FactProductETL(
            bucket     = os.getenv("S3_BUCKET"),
            raw_prefix = "raw",
            year       = yr,
            month      = mo,
            day        = dy
        )
        df_fact = etl.load_fact_products()

        # use the exact partitions that ETL used
        y,m,d = etl.year, etl.month, etl.day

        # build destination key using those partitions
        s3_key = (
            f"fact_product_shoes/"
            f"{y:04d}/"
            f"{m:02d}/"
            f"{d:02d}/"
            "fact_products.parquet"
        )

        out_uri = ParquetUtil.upload_df_to_s3_parquet(
            df     = df_fact,
            bucket = os.getenv("S3_BUCKET"),
            s3_key = s3_key
        )

        logger.info(f"Uploaded fact data to {out_uri}")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "rows": len(df_fact),
                "s3_path": out_uri
            }),
            "headers": {"Content-Type": "application/json"}
        }

    except Exception:
        logger.exception("ETL failed")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "ETL failed, see logs"}),
            "headers": {"Content-Type": "application/json"}
        }
