# handlers/quality.py

import os
import json
import logging
import pandas as pd
from dotenv import load_dotenv

from quality.nike import NikeQuality
from quality.worldbalance import WorldBalanceQuality
from quality.hoka import HokaQuality

logger = logging.getLogger()
logger.setLevel(logging.INFO)

if os.getenv("ENV_MODE") == "DEV":
    load_dotenv()

QUALITY_MAP = {
    "nike":        NikeQuality,
    "worldbalance": WorldBalanceQuality,
    "hoka":        HokaQuality
}

def lambda_handler(event, context):
    logger.info(">>> quality.lambda_handler start")
    params = event.get("queryStringParameters") or json.loads(event.get("body","{}"))
    brand       = params.get("brand","").lower()
    cleaned_key = params.get("cleaned_s3_key")

    if brand not in QUALITY_MAP:
        logger.error(f"Unsupported brand '{brand}'")
        return respond(400, {"error": f"Unsupported brand '{brand}'."})
    if not cleaned_key:
        logger.error("Missing cleaned_s3_key")
        return respond(400, {"error": "'cleaned_s3_key' is required."})

    bucket = os.environ["S3_BUCKET"]
    s3_uri = f"s3://{bucket}/{cleaned_key}"
    logger.info(f"Reading cleaned CSV from {s3_uri}")
    df = pd.read_csv(s3_uri)

    quality = QUALITY_MAP[brand]()
    passed, details = quality.run(df)

    logger.info(f"Quality results for {brand}: passed={passed}, details={details}")

    return respond(200, {
        "quality_passed": passed,
        "rows": len(df),
        "details": details
    })

def respond(status_code, body):
    return {
        "statusCode": status_code,
        "body":       json.dumps(body),
        "headers":    {"Content-Type":"application/json"}
    }
