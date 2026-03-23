import os

TARGET_ROLE_ARN = os.getenv(
    "TARGET_ROLE_ARN",
    "arn:aws:iam::000000000000:role/REPLACE_ME",
)

DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
