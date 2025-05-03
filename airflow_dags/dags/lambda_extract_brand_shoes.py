# lambda_extract_brand_shoes.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.sensors.s3_key import S3KeySensor
from datetime import datetime, timedelta
from utils.secrets_util import get_secret
import boto3
import json

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'ph_shoes_etl',
    default_args=default_args,
    schedule_interval="0 12 * * *",
    catchup=False,
) as dag:

    def _get_lambda_client():
        creds = get_secret()
        return boto3.client(
            'lambda',
            region_name=creds.get('AWS_REGION','ap-southeast-1'),
            aws_access_key_id=creds['AWS_LAMBDA_INVOKER_ACCESS_KEY_ID'],
            aws_secret_access_key=creds['AWS_LAMBDA_INVOKER_SECRET_ACCESS_KEY'],
        )

    def extract_async(brand, **kwargs):
        payload = {"queryStringParameters": {"brand": brand, "category": "all", "pages": "-1"}}
        _get_lambda_client().invoke(
            FunctionName="ph-shoes-extract-lambda",
            InvocationType='Event',
            Payload=json.dumps(payload).encode(),
        )
        today = datetime.utcnow()
        return f"raw/{today:%Y}/{today:%m}/{today:%d}/{brand}_all_extracted.csv"

    def clean_task(brand, ti, **kwargs):
        raw_key = ti.xcom_pull(task_ids=f"extract_{brand}")
        payload = {"queryStringParameters": {"brand": brand, "raw_s3_key": raw_key}}
        resp = _get_lambda_client().invoke(
            FunctionName="ph-shoes-clean-lambda",
            InvocationType='RequestResponse',
            Payload=json.dumps(payload).encode(),
        )
        data = json.loads(resp['Payload'].read())
        body = json.loads(data['body'])
        return body['cleaned_s3_key']

    def quality_task(brand, ti, **kwargs):
        cleaned = ti.xcom_pull(task_ids=f"clean_{brand}")
        payload = {"queryStringParameters": {"brand": brand, "cleaned_s3_key": cleaned}}
        resp = _get_lambda_client().invoke(
            FunctionName="ph-shoes-quality-lambda",
            InvocationType='RequestResponse',
            Payload=json.dumps(payload).encode(),
        )
        data = json.loads(resp['Payload'].read())
        body = json.loads(data['body'])
        if not body.get("quality_passed", False):
            raise RuntimeError(f"Quality failed for {brand}")
        return True

    BRANDS = ["worldbalance", "nike", "hoka"]

    for brand in BRANDS:
        t_extract = PythonOperator(
            task_id=f"extract_{brand}",
            python_callable=extract_async,
            op_kwargs={"brand": brand},
        )

        t_wait = S3KeySensor(
            task_id=f"wait_for_{brand}_extracted",
            bucket_key="{{ ti.xcom_pull(task_ids='extract_" + brand + "') }}",
            wildcard_match=False,
            bucket_name="ph-shoes-data-lake",
            poke_interval=30,
            timeout=60*15,
        )

        t_clean = PythonOperator(
            task_id=f"clean_{brand}",
            python_callable=clean_task,
            op_kwargs={"brand": brand},
        )

        t_quality = PythonOperator(
            task_id=f"quality_{brand}",
            python_callable=quality_task,
            op_kwargs={"brand": brand},
        )

        t_extract >> t_wait >> t_clean >> t_quality
