from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from utils.secrets_util import get_secret
import boto3
import json

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    # start_date in UTC (we convert 8:00 PM PH to UTC: 8:00 PM PH = 12:00 PM UTC)
    'start_date': datetime(2024, 1, 1, 12, 0),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Schedule interval in UTC so that the DAG runs daily at 8:00 PM PH Time (12:00 UTC)
dag = DAG(
    'lambda_invoker_dag',
    default_args=default_args,
    description='A DAG to call Lambda functions daily',
    schedule_interval="0 12 * * *",
    catchup=False,
)

def invoke_lambda_function(lambda_name, payload=None):
    creds = get_secret()

    client = boto3.client(
        'lambda',
        region_name=creds.get('AWS_REGION', 'ap-southeast-1'),
        aws_access_key_id=creds.get('AWS_LAMBDA_INVOKER_ACCESS_KEY_ID'),
        aws_secret_access_key=creds.get('AWS_LAMBDA_INVOKER_SECRET_ACCESS_KEY')
    )

    if payload is None:
        payload = {}

    client.invoke(
        FunctionName=lambda_name,
        InvocationType='Event',
        Payload=json.dumps(payload).encode()
    )

    print(f"Lambda {lambda_name} invoked.")
    # Do not return anything to avoid XCom serialization issues


# Task to invoke worldbalance Lambda
invoke_worldbalance = PythonOperator(
    task_id='invoke_worldbalance_lambda',
    python_callable=invoke_lambda_function,
    op_kwargs={
        'lambda_name': 'worldbalance-lambda',  # Change if your Lambda name is different
        'payload': {
            "queryStringParameters": {
                "brand": "worldbalance",
                "category": "all",
                "pages": "-1"
            }
        }
    },
    dag=dag,
)

# Task to invoke nike Lambda
invoke_nike = PythonOperator(
    task_id='invoke_nike_lambda',
    python_callable=invoke_lambda_function,
    op_kwargs={
        'lambda_name': 'nike-lambda',  # Change if your Lambda name is different
        'payload': {
            "queryStringParameters": {
                "brand": "nike",
                "category": "all",
                "pages": "-1"
            }
        }
    },
    dag=dag,
)

# Task to invoke hoka Lambda
invoke_hoka = PythonOperator(
    task_id='invoke_hoka_lambda',
    python_callable=invoke_lambda_function,
    op_kwargs={
        'lambda_name': 'hoka-lambda',
        'payload': {
            "queryStringParameters": {
                "brand": "hoka",
                "category": "all",
                "pages": "-1"
            }
        }
    },
    dag=dag,
)

