# handlers/clean.py

import os
import json
import logging
import pandas as pd
import boto3
from urllib.parse import urlparse
from dotenv import load_dotenv

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

_s3 = boto3.client("s3")

def lambda_handler(event, context):
    logger.info("Lambda pure-clean started…")
    try:
        body    = event.get("queryStringParameters") or json.loads(event.get("body","{}"))
        brand   = body.get("brand","").lower()
        raw_ref = body.get("raw_s3_key","")

        if brand not in CLEANER_MAP:
            return respond(400, {"error": f"Unsupported brand '{brand}'."})
        if not raw_ref:
            return respond(400, {"error": "'raw_s3_key' is required."})

        # parse S3 URI or raw key
        if raw_ref.startswith("s3://"):
            u      = urlparse(raw_ref)
            bucket = u.netloc
            key    = u.path.lstrip("/")
        else:
            bucket = os.environ["S3_BUCKET"]
            key    = raw_ref

        # read CSV via boto3 (no fsspec required)
        resp   = _s3.get_object(Bucket=bucket, Key=key)
        df_raw = pd.read_csv(resp["Body"])

        # clean
        cleaner  = CLEANER_MAP[brand]()
        df_clean = cleaner.clean(df_raw)

        # build cleaned key under same folder
        folder, fname = key.rsplit("/",1) if "/" in key else ("", key)
        cleaned_fname = fname.replace("_extracted.csv","_cleaned.csv")
        cleaned_key   = f"{folder}/{cleaned_fname}" if folder else cleaned_fname

        # upload cleaned CSV
        CSVUtil.upload_df_to_s3(df_clean, cleaned_key)

        return respond(200, {
            "cleaned_count":    len(df_clean),
            "cleaned_s3_key":   cleaned_key,
            "cleaned_s3_uri":   f"s3://{bucket}/{cleaned_key}"
        })

    except Exception:
        logger.exception("Error during cleaning")
        return respond(500, {"error":"Internal cleaning failure"})

def respond(status_code, body):
    return {
        "statusCode": status_code,
        "body":       json.dumps(body),
        "headers":    {"Content-Type":"application/json"}
    }
