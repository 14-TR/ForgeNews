# Standard library imports
import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

# Third-party imports
import boto3
from botocore.exceptions import ClientError

# Local application imports
from aws_config import AWSConfig

class AWSSecretManager:
    """Centralized AWS Secrets Manager handler"""
    
    def __init__(self, config: AWSConfig = AWSConfig()):
        self.config = config
        self.session = boto3.session.Session()
        self.client = self.session.client(
            service_name='secretsmanager',
            region_name=self.config.REGION_NAME
        )

    def _get_secret(self, secret_name: str) -> Optional[Dict]:
        """
        Generic method to retrieve and parse a secret
        """
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return json.loads(response["SecretString"])
        except ClientError as e:
            print(f"❌ Error retrieving secret '{secret_name}': {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing secret '{secret_name}': {e}")
            return None

    def get_db_credentials(self) -> Optional[Dict]:
        """
        Retrieve database credentials from AWS Secrets Manager
        """
        secret = self._get_secret(self.config.DB_SECRET_NAME)
        if secret and "DB_CONFIG" in secret and isinstance(secret["DB_CONFIG"], dict):
            return secret["DB_CONFIG"]
        print("❌ Error: DB_CONFIG key is missing or improperly formatted.")
        return None

    def get_openai_api_key(self) -> Optional[str]:
        """
        Retrieve OpenAI API key from AWS Secrets Manager
        """
        secret = self._get_secret(self.config.OPENAI_SECRET_NAME)
        if secret and "OPENAI_API_KEY" in secret:
            return secret["OPENAI_API_KEY"]
        return None

    def get_viirs_secrets(self) -> Optional[List[str]]:
        """
        Retrieve VIIRS API keys from AWS Secrets Manager
        Returns:
            Optional[List[str]]: List of VIIRS MAP_KEYs if successful, None otherwise
        """
        secret = self._get_secret(self.config.VIIRS_SECRET_NAME)
        if secret:
            api_keys = [value for key, value in secret.items() if key.startswith('viirs_map_key')]
            if api_keys:
                return api_keys
            print("❌ Error: No VIIRS API keys found in secrets")
        return None

def get_aws_credentials() -> Dict[str, str]:
    """
    Get AWS credentials from environment variables
    Returns:
        Dict containing AWS credentials and region
    """
    return {
        'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
        'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
        'region_name': os.getenv('AWS_REGION', AWSConfig.REGION_NAME)
    }

# # Example usage:
# if __name__ == "__main__":
#     # Initialize with default config
#     secret_manager = AWSSecretManager()
    
#     # Or initialize with custom config
#     custom_config = AWSConfig(
#         REGION_NAME="us-west-2",
#         DB_SECRET_NAME="custom-db-config",
#         OPENAI_SECRET_NAME="custom-openai",
#         VIIRS_SECRET_NAME="custom-viirs"
#     )
#     custom_secret_manager = AWSSecretManager(custom_config)

