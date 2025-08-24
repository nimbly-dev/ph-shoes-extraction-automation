# utils/csv_util.py
import os
import csv
import boto3
import io
from dataclasses import asdict, is_dataclass
from typing import List, Union, Dict, Any

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
    def upload_to_s3(results, save_location: str) -> str:
        # Build CSV in-memory
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(results[0].__dict__.keys())
        for shoe in results:
            writer.writerow(shoe.__dict__.values())
        csv_content = out.getvalue()
        out.close()

        # Use Lambda's IAM role — NO static keys
        s3 = boto3.client("s3")

        s3_bucket = os.getenv("S3_BUCKET")
        if not s3_bucket or not isinstance(s3_bucket, str):
            raise ValueError("S3_BUCKET environment variable is not set properly as a string.")

        s3.put_object(Bucket=s3_bucket, Key=save_location, Body=csv_content.encode("utf-8"))
        return save_location
