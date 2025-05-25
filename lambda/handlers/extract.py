import os
import json
import logging
from dotenv import load_dotenv
from dataclasses import asdict
from datetime import datetime


# Import extractors
from extractors.nike import NikeExtractor
from extractors.world_balance import WorldBalanceExtractor
from extractors.hoka import HokaExtractor
from utils.csv_util import CSVUtil

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Load .env in dev container
if os.getenv("ENV_MODE") == "DEV":
    load_dotenv()

# Mapping of supported brands to extractors
EXTRACTOR_MAP = {
    "nike": NikeExtractor,
    "worldbalance": WorldBalanceExtractor,
    "hoka": HokaExtractor,
}

def lambda_handler(event, context):
    logger.info("Lambda extractor started...")

    try:
        # --- Extract Query Params ---
        query_params = event.get("queryStringParameters", {})
        category = query_params.get("category")
        brand = query_params.get("brand", "adidas").lower()
        pages = int(query_params.get("pages", -1))

        if not category:
            return respond(400, {"error": "'category' query parameter is required."})

        if brand not in EXTRACTOR_MAP:
            return respond(400, {"error": f"Brand '{brand}' not implemented."})

        # --- Run Extraction ---
        extractor_class = EXTRACTOR_MAP[brand]
        extractor = extractor_class(category, pages)
        results = extractor.extract()

        # --- Upload to S3 ---
        now = datetime.utcnow()
        save_location = f"raw/{now.year}/{now.month:02d}/{now.day:02d}/{brand}_{category}_extracted.csv"
        s3_key = CSVUtil.upload_to_s3(results, save_location)

        return respond(200, {
            "extracted": [asdict(shoe) for shoe in results],
            "s3_upload": f"successful: {s3_key}"
        })

    except Exception as e:
        logger.exception("Lambda error")
        return respond(500, {"error": str(e)})


def respond(status_code, body_dict):
    return {
        "statusCode": status_code,
        "body": json.dumps(body_dict),
        "headers": {"Content-Type": "application/json"}
    }
