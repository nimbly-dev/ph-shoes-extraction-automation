import json
import boto3
from botocore.exceptions import ClientError

class SecretsUtil:
    # class‑level cache: { (secret_name, region) → dict }
    _cache: dict[tuple[str,str], dict] = {}

    @staticmethod
    def get_secret(secret_name: str = "prod/shoes-data-lake-creds",
                   region: str = "ap-southeast-1") -> dict:
        """
        Fetch & cache a JSON secret from AWS Secrets Manager.
        Subsequent calls with the same (secret_name, region) return the in‑memory dict.
        """
        key = (secret_name, region)
        if key in SecretsUtil._cache:
            return SecretsUtil._cache[key]

        client = boto3.client("secretsmanager", region_name=region)
        try:
            resp = client.get_secret_value(SecretId=secret_name)
        except client.exceptions.ResourceNotFoundException:
            raise ValueError(f"Secret {secret_name} not found")
        except client.exceptions.InvalidRequestException as e:
            raise ValueError(f"Invalid request: {e}")
        except client.exceptions.InvalidParameterException as e:
            raise ValueError(f"Invalid parameter: {e}")
        except ClientError as e:
            raise ValueError(f"Error retrieving secret {secret_name}: {e}")

        try:
            secret_dict = json.loads(resp["SecretString"])
        except (KeyError, json.JSONDecodeError) as e:
            raise ValueError(f"Secret {secret_name} did not contain valid JSON: {e}")

        # cache and return
        SecretsUtil._cache[key] = secret_dict
        return secret_dict
