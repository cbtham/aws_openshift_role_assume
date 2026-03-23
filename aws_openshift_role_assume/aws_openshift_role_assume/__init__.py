__version__ = "0.1.0"

from .aws import client, resource, get_boto3_session
from .identity import get_user

__all__ = ["client", "resource", "get_boto3_session", "get_user"]
