from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
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

dag = DAG(
    'ph_shoes_etl',
    default_args=default_args,
    schedule_interval="0 12 * * *",
    catchup=False,
)

def _get_lambda_client():
    creds = get_secret()
    return boto3.client(
        'lambda',
        region_name=creds.get('AWS_REGION', 'ap-southeast-1'),
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
    payload = {
        "queryStringParameters": {
            "brand": brand,
            "category": "all",
            "pages": "-1"
        }
    }
    body = invoke_lambda("ph-shoes-extract-lambda", payload)
    key = body.get("extracted_s3_key") or (body.get("s3_upload", "").split()[-1] if body.get("s3_upload") else None)
    if not key:
        raise RuntimeError("no extracted_s3_key returned")
    return key

def clean_task(brand, ti, **kwargs):
    raw_key = ti.xcom_pull(task_ids=f"extract_{brand}")
    payload = {
        "queryStringParameters": {
            "brand": brand,
            "raw_s3_key": raw_key
        }
    }
    body = invoke_lambda("ph-shoes-clean-lambda", payload)
    cleaned = body.get("cleaned_s3_key")
    if not cleaned:
        raise RuntimeError("no cleaned_s3_key returned")
    return cleaned

def quality_task(brand, ti, **kwargs):
    cleaned_key = ti.xcom_pull(task_ids=f"clean_{brand}")
    payload = {
        "queryStringParameters": {
            "brand": brand,
            "cleaned_s3_key": cleaned_key
        }
    }
    body = invoke_lambda("ph-shoes-quality-lambda", payload)
    if not body.get("quality_passed", False):
        raise RuntimeError(f"Quality failed for {brand}")
    return True

BRANDS = ["nike", "hoka", "worldbalance"]

# build extract → clean → quality for each brand
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

# After all quality tasks, run dbt
dbt_run = BashOperator(
    task_id="run_dbt_models",
    bash_command=(
        "dbt run --models +fact_product_shoes "
        "--vars '{"
          "\"year\":\"{{ ds.split('-',2)[0] }}\","
          "\"month\":\"{{ ds.split('-',2)[1] }}\","
          "\"day\":\"{{ ds.split('-',2)[2] }}\""
        "}'"
    ),
    dag=dag,
)

# chain every quality_<brand> into dbt_run
for brand in BRANDS:
    dag.get_task(f"quality_{brand}") >> dbt_run
