# utils/parquet_util.py

import os
import io
import boto3
import pandas as pd

class ParquetUtil:
    @staticmethod
    def upload_df_to_s3_parquet(
        df: pd.DataFrame,
        bucket: str,
        s3_key: str
    ) -> str:
        """
        Write `df` as a single Parquet file to s3://{bucket}/{s3_key}.
        All object columns will be cast to string (null → "").
        """
        # Convert any object‑dtype column into string, fill nulls
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].fillna("").astype(str)

        # write to in‑memory buffer
        buffer = io.BytesIO()
        df.to_parquet(buffer, engine="pyarrow", index=False)
        buffer.seek(0)

        # upload to S3
        boto3.client("s3").put_object(Bucket=bucket, Key=s3_key, Body=buffer.getvalue())
        return f"s3://{bucket}/{s3_key}"
