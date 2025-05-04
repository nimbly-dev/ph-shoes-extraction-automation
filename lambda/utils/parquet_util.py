import os
import io
import boto3
import pandas as pd

import os
import io
import json
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
        Any columns containing list or dict objects will be JSON‑serialized.
        """
        # JSON‑serialize list/dict columns
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].apply(
                    lambda x: json.dumps(x) if isinstance(x, (list, dict)) else x
                )

        # write to an in‑memory buffer
        buffer = io.BytesIO()
        df.to_parquet(buffer, engine="pyarrow", index=False)
        buffer.seek(0)

        # upload
        s3 = boto3.client("s3")
        s3.put_object(Bucket=bucket, Key=s3_key, Body=buffer.getvalue())

        return f"s3://{bucket}/{s3_key}"