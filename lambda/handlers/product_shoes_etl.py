
import os, json, logging
from datetime import datetime
from fact_product_shoes.fact_product_shoes import FactProductETL  
from utils.csv_util import CSVUtil

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("FactProductETL Lambda started…")

    # optional: override via query params
    params = event.get("queryStringParameters") or {}
    yr = int(params.get("year",  os.getenv("ETL_YEAR",  0))) or None
    mo = int(params.get("month", os.getenv("ETL_MONTH", 0))) or None
    dy = int(params.get("day",   os.getenv("ETL_DAY",   0))) or None

    try:
        etl = FactProductETL(
            raw_base = "raw",
            year     = yr,
            month    = mo,
            day      = dy
        )
        df_fact = etl.load_fact_products()
        records = df_fact.to_dict(orient="records")

        now = datetime.utcnow()
        key = (
            f"fact_product_shoes/"
            f"year={now.year:04d}/month={now.month:02d}/day={now.day:02d}/"
            "fact_products.csv"
        )

        s3_key = CSVUtil.upload_to_s3(records, key)
        logger.info(f"Uploaded fact to s3://{s3_key}")

        return {
            "statusCode": 200,
            "body": json.dumps({"rows": len(records), "s3_key": s3_key}),
            "headers": {"Content-Type": "application/json"}
        }

    except Exception:
        logger.exception("ETL failed")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "ETL failed, see logs"}),
            "headers": {"Content-Type": "application/json"}
        }
