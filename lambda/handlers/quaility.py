# handlers/quality.py

import os
import json
import logging
import pandas as pd
from dotenv import load_dotenv

from utils.csv_util import CSVUtil
from quality.nike import NikeQuality
from quality.worldbalance import WorldBalanceQuality
from quality.hoka import HokaQuality

logger = logging.getLogger()
logger.setLevel(logging.INFO)

if os.getenv("ENV_MODE") == "DEV":
    load_dotenv()

QUALITY_MAP = {
    "nike": NikeQuality,
    "worldbalance": WorldBalanceQuality,
    "hoka": HokaQuality
}

def lambda_handler(event, context):
    body = event.get("queryStringParameters") or json.loads(event.get("body","{}"))
    brand      = body.get("brand","").lower()
    cleaned_key = body.get("cleaned_s3_key")
    if brand not in QUALITY_MAP:
        return respond(400, {"error": f"Unsupported brand '{brand}'."})
    if not cleaned_key:
        return respond(400, {"error": "'cleaned_s3_key' is required."})
    bucket = os.environ["S3_BUCKET"]
    df = CSVUtil.read_df_from_s3(bucket, cleaned_key)
    quality = QUALITY_MAP[brand]()
    passed = quality.run(df)
    return respond(200, {"quality_passed": passed, "rows": len(df)})

def respond(status_code, body):
    return {
        "statusCode": status_code,
        "body": json.dumps(body),
        "headers": {"Content-Type":"application/json"}
    }
