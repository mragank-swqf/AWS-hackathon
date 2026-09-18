import os

import boto3
from botocore.config import Config


def client(service: str):
    endpoint = os.environ["AWS_ENDPOINT_URL"]
    return boto3.client(
        service,
        endpoint_url=endpoint,
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        config=Config(s3={"addressing_style": "path"}),
    )
