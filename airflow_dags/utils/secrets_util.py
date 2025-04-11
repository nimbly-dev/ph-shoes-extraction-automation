import os
import json
import boto3
from dotenv import load_dotenv

# Load .env file if exists (for local development)
load_dotenv()

def get_secret(secret_name="prod/ph-shoes/s3-credentials", region="ap-southeast-1"):
    """
    Attempts to retrieve a secret from AWS Secrets Manager.
    Falls back to .env if not running in a production environment or if secret not found.
    """
    env_mode = os.getenv("ENV_MODE", "DEV")
    if env_mode.upper() == "DEV":
        # For development, return secrets from .env
        return {
            "AWS_LAMBDA_INVOKER_ACCESS_KEY_ID": os.getenv("AWS_LAMBDA_INVOKER_ACCESS_KEY_ID"),
            "AWS_LAMBDA_INVOKER_SECRET_ACCESS_KEY": os.getenv("AWS_LAMBDA_INVOKER_SECRET_ACCESS_KEY"),
            "AWS_REGION": os.getenv("AWS_REGION", region)
        }
    
    # For production, attempt to fetch from Secrets Manager
    try:
        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response["SecretString"])
    except Exception as e:
        raise Exception(f"Failed to retrieve secret {secret_name}: {str(e)}")
