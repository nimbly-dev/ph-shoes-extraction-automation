import json
import boto3


class SecretsUtil:
    
    @staticmethod
    def get_secret(secret_name="prod/shoes-data-lake-creds", region="ap-southeast-1"):
        client = boto3.client("secretsmanager", region_name=region)
        try:
            response = client.get_secret_value(SecretId=secret_name)
        except client.exceptions.ResourceNotFoundException:
            raise ValueError(f"Secret {secret_name} not found")
        except client.exceptions.InvalidRequestException as e:
            raise ValueError(f"Invalid request: {str(e)}")
        except client.exceptions.InvalidParameterException as e:
            raise ValueError(f"Invalid parameter: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error retrieving secret {secret_name}: {str(e)}")
        return json.loads(response["SecretString"])