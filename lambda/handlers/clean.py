# handlers/clean.py

import os
import json
import logging
import pandas as pd
from dotenv import load_dotenv
from dataclasses import asdict

from utils.csv_util import CSVUtil
from clean.worldbalance import WorldBalanceCleaner
from clean.hoka import HokaCleaner
from clean.nike import NikeCleaner

logger = logging.getLogger()
logger.setLevel(logging.INFO)

if os.getenv("ENV_MODE") == "DEV":
    load_dotenv()

CLEANER_MAP = {
    "nike": NikeCleaner,
    "worldbalance": WorldBalanceCleaner,
    "hoka": HokaCleaner
}


def lambda_handler(event, context):
    """
    event should contain JSON:
      {
        "brand": "nike",
        "raw_s3_key": "nike_running013_extracted.csv"
      }
    """
    logger.info("Lambda pure-clean started…")
    try:
        body = event.get("queryStringParameters") or json.loads(event.get("body","{}"))
        brand     = body.get("brand", "").lower()
        raw_key   = body.get("raw_s3_key")

        if brand not in CLEANER_MAP:
            return respond(400, {"error": f"Unsupported brand '{brand}'."})
        if not raw_key:
            return respond(400, {"error": "'raw_s3_key' is required."})

        bucket = os.environ["S3_BUCKET"]
        df_raw = CSVUtil.read_df_from_s3(bucket, raw_key)

        # clean
        cleaner = CLEANER_MAP[brand]()
        df_clean = cleaner.clean(df_raw)

        # write cleaned CSV back to S3
        cleaned_key = raw_key.replace("_extracted.csv", "_cleaned.csv")
        CSVUtil.upload_df_to_s3(df_clean, cleaned_key)

        return respond(200, {
            "cleaned_count": len(df_clean),
            "cleaned_s3_key": cleaned_key
        })

    except Exception:
        logger.exception("Error during cleaning")
        return respond(500, {"error": "Internal cleaning failure"})


def respond(status_code, body):
    return {
        "statusCode": status_code,
        "body": json.dumps(body),
        "headers": {"Content-Type": "application/json"}
    }