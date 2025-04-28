from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from utils.secrets_util import get_secret
import boto3
import json

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    # 8:00 PM PH time → 12:00 UTC
    'start_date': datetime(2024, 1, 1, 12, 0),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'lambda_invoker_dag',
    default_args=default_args,
    description='Invoke the ph-shoes-extract-lambda for each brand daily',
    schedule_interval="0 12 * * *",
    catchup=False,
)

def invoke_lambda_function(lambda_name, payload=None):
    creds = get_secret()
    client = boto3.client(
        'lambda',
        region_name=creds.get('AWS_REGION', 'ap-southeast-1'),
        aws_access_key_id=creds['AWS_LAMBDA_INVOKER_ACCESS_KEY_ID'],
        aws_secret_access_key=creds['AWS_LAMBDA_INVOKER_SECRET_ACCESS_KEY'],
    )
    if payload is None:
        payload = {}
    client.invoke(
        FunctionName=lambda_name,
        InvocationType='Event',
        Payload=json.dumps(payload).encode(),
    )
    print(f"Invoked Lambda: {lambda_name} with payload {payload!r}")

# Single function name you actually have
FUNCTION_NAME = "ph-shoes-extract-lambda"

# Prepare brand-specific payloads
BRAND_PAYLOADS = {
    'worldbalance': {
        "queryStringParameters": {
            "brand": "worldbalance",
            "category": "all",
            "pages": "-1"
        }
    },
    'nike': {
        "queryStringParameters": {
            "brand": "nike",
            "category": "all",
            "pages": "-1"
        }
    },
    'hoka': {
        "queryStringParameters": {
            "brand": "hoka",
            "category": "all",
            "pages": "-1"
        }
    },
}

# Dynamically create one task per brand
for brand, payload in BRAND_PAYLOADS.items():
    PythonOperator(
        task_id=f"invoke_{brand}_lambda",
        python_callable=invoke_lambda_function,
        op_kwargs={
            'lambda_name': FUNCTION_NAME,
            'payload': payload,
        },
        dag=dag,
    )
