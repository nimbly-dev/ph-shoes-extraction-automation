from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from airflow.utils.dates import days_ago
import requests
from utils.secrets_util import get_secret   # we’ll reuse get_secret for both Lambda creds and dbt creds
import boto3
from botocore.config import Config  # ← add this
import json

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'ph_shoes_etl',
    default_args=default_args,
    schedule_interval="0 12 * * *",
    catchup=False,
)

def _get_lambda_client():
    creds = get_secret("prod/ph-shoes/s3-credentials")  # or whatever your secret name is
    lambda_cfg = Config(
        region_name=creds.get('AWS_REGION', 'ap-southeast-1'),
        connect_timeout=60,    # time to establish the TCP socket
        read_timeout=300       # time to wait for the HTTP response
    )
    return boto3.client(
        'lambda',
        config=lambda_cfg,
        aws_access_key_id=creds['AWS_LAMBDA_INVOKER_ACCESS_KEY_ID'],
        aws_secret_access_key=creds['AWS_LAMBDA_INVOKER_SECRET_ACCESS_KEY'],
    )


def invoke_lambda(lambda_name, payload):
    client = _get_lambda_client()
    resp = client.invoke(
        FunctionName=lambda_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload).encode(),
    )
    data = json.loads(resp['Payload'].read())
    body = data.get('body', data)
    if isinstance(body, str):
        body = json.loads(body)
    if data.get('FunctionError'):
        raise RuntimeError(f"{lambda_name} error: {body}")
    return body

def extract_task(brand, **kwargs):
    payload = {"queryStringParameters": {"brand": brand, "category": "all", "pages": "-1"}}
    body = invoke_lambda("ph-shoes-extract-lambda", payload)
    key = body.get("extracted_s3_key") or (body.get("s3_upload", "").split()[-1] if body.get("s3_upload") else None)
    if not key:
        raise RuntimeError("no extracted_s3_key returned")
    return key

def clean_task(brand, ti, **kwargs):
    raw_key = ti.xcom_pull(task_ids=f"extract_{brand}")
    payload = {"queryStringParameters": {"brand": brand, "raw_s3_key": raw_key}}
    body = invoke_lambda("ph-shoes-clean-lambda", payload)
    cleaned = body.get("cleaned_s3_key")
    if not cleaned:
        raise RuntimeError("no cleaned_s3_key returned")
    return cleaned

def quality_task(brand, ti, **kwargs):
    cleaned_key = ti.xcom_pull(task_ids=f"clean_{brand}")
    payload = {"queryStringParameters": {"brand": brand, "cleaned_s3_key": cleaned_key}}
    body = invoke_lambda("ph-shoes-quality-lambda", payload)
    if not body.get("quality_passed", False):
        raise RuntimeError(f"Quality failed for {brand}")
    return True

# BRANDS = ["nike", "hoka", "worldbalance"]
BRANDS = ["worldbalance"]

# chain extract → clean → quality for each brand
for brand in BRANDS:
    t0 = PythonOperator(
        task_id=f"extract_{brand}",
        python_callable=extract_task,
        op_kwargs={"brand": brand},
        dag=dag,
    )
    t1 = PythonOperator(
        task_id=f"clean_{brand}",
        python_callable=clean_task,
        op_kwargs={"brand": brand},
        dag=dag,
    )
    t2 = PythonOperator(
        task_id=f"quality_{brand}",
        python_callable=quality_task,
        op_kwargs={"brand": brand},
        dag=dag,
    )
    t0 >> t1 >> t2

def trigger_dbt_cloud(**kwargs):
    execution_date = kwargs["execution_date"]
    year, month, day = execution_date.year, execution_date.month, execution_date.day

    creds = get_secret("prod/ph-shoes/dbt-credentials")
    acct = creds["DBT_CLOUD_ACCOUNT_ID"]
    job  = creds["DBT_CLOUD_JOB_ID"]
    token= creds["DBT_API_TOKEN"]

    run_cmd = (
        "dbt run --models +fact_product_shoes "
        f"--vars '{{\"year\":{year},\"month\":{month},\"day\":{day}}}'"
    )

    payload = {
      "cause": "Triggered via Airflow DAG",
      "steps_override": [ run_cmd ]
    }

    url = f"https://cloud.getdbt.com/api/v2/accounts/{acct}/jobs/{job}/run/"
    headers = {
      "Authorization": f"Token {token}",
      "Content-Type": "application/json"
    }
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    run_id = resp.json()["data"]["id"]
    return run_id

dbt_cloud_trigger = PythonOperator(
    task_id="trigger_dbt_cloud_job",
    python_callable=trigger_dbt_cloud,
    dag=dag,
)

# run dbt trigger only after all quality tasks
for brand in BRANDS:
    dag.get_task(f"quality_{brand}") >> dbt_cloud_trigger
