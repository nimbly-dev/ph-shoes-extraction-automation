import os
import csv
import boto3
import io 
from datetime import datetime
from dataclasses import asdict, is_dataclass
from typing import List, Union, Dict, Any
from utils.secrets_util import SecretsUtil

class CSVUtil:

    @staticmethod
    def write_to_csv(data: List[Union[Dict[str, Any], object]], filename: str, fieldnames: List[str] = None):
        dict_data = []
        for item in data:
            if is_dataclass(item):
                dict_data.append(asdict(item))
            elif isinstance(item, dict):
                dict_data.append(item)
            else:
                raise ValueError("Data must be either a dictionary or a dataclass instance")

        if not dict_data:
            raise ValueError("No data provided to write.")

        if not fieldnames:
            fieldnames = list(dict_data[0].keys())

        with open(filename, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in dict_data:
                writer.writerow(row)

    @staticmethod
    def upload_to_s3(results, file_name: str):
        # Create CSV content in memory
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(results[0].__dict__.keys())
        for shoe in results:
            writer.writerow(shoe.__dict__.values())
        csv_content = output.getvalue()
        output.close()

        # Format S3 key
        now = datetime.utcnow()
        s3_key = f"raw/{now.year}/{now.month:02d}/{now.day:02d}/{file_name}"

        secrets = SecretsUtil.get_secret(secret_name="prod/ph-shoes/s3-credentials")

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=secrets["AWS_S3_DATA_LAKE_UPLOADER_ACCESS_KEY_ID"],
            aws_secret_access_key=secrets["AWS_S3_DATA_LAKE_UPLOADER_SECRET_ACCESS_KEY"],
            region_name="ap-southeast-1"
        )

        s3_bucket = os.getenv("S3_BUCKET")
        if not s3_bucket or not isinstance(s3_bucket, str):
            raise ValueError("S3_BUCKET environment variable is not set properly as a string.")

        s3_client.put_object(Bucket=s3_bucket, Key=s3_key, Body=csv_content)
        return s3_key