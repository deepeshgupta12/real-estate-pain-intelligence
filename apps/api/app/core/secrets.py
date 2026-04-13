"""
Secrets management layer. In production, reads from environment or
a secrets manager. In development, falls back to .env file values.

Usage:
    from app.core.secrets import get_secret
    db_url = get_secret("DATABASE_URL")
"""
import os
import logging

logger = logging.getLogger(__name__)


def get_secret(key: str, default: str | None = None) -> str | None:
    """
    Retrieve a secret value. Priority:
    1. AWS Secrets Manager (if AWS_SECRET_ARN env var is set)
    2. GCP Secret Manager (if GCP_PROJECT_ID env var is set)
    3. Environment variable
    4. Default value
    """
    # Try AWS Secrets Manager
    aws_arn = os.getenv("AWS_SECRET_ARN")
    if aws_arn:
        try:
            import boto3
            import json
            client = boto3.client("secretsmanager")
            response = client.get_secret_value(SecretId=aws_arn)
            secrets = json.loads(response["SecretString"])
            if key in secrets:
                return secrets[key]
        except Exception as exc:
            logger.warning(f"AWS Secrets Manager lookup failed: {exc}")

    # Try GCP Secret Manager
    gcp_project = os.getenv("GCP_PROJECT_ID")
    if gcp_project:
        try:
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{gcp_project}/secrets/{key}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("utf-8")
        except Exception as exc:
            logger.warning(f"GCP Secret Manager lookup failed: {exc}")

    # Fall back to environment variable
    return os.getenv(key, default)
