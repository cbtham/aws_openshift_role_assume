import logging
import boto3
from botocore.credentials import RefreshableCredentials
from botocore.session import get_session

from .identity import get_user
from .config import TARGET_ROLE_ARN, DEFAULT_REGION

logger = logging.getLogger(__name__)

def _fetch_credentials():
    """
    Calls STS AssumeRole using the base IRSA credentials mapped to the pod.
    Tags the session with the current user's identity so IAM/S3 policies can 
    dynamically enforce dataset access tiers (e.g. bronze/silver/gold/diamond).
    """
    user = get_user()
    # Handle kubernetes character restrictions in labels
    if user == "kube-3aadmin":
        user = "kube-admin"
        
    sts = boto3.client('sts', region_name=DEFAULT_REGION)
    
    # Tag the session with the user identity
    tags = [
        {"Key": "user", "Value": user}
    ]
    
    response = sts.assume_role(
        RoleArn=TARGET_ROLE_ARN,
        RoleSessionName=user,
        Tags=tags,
        DurationSeconds=3600
    )
    
    creds = response['Credentials']
    
    return {
        'access_key': creds['AccessKeyId'],
        'secret_key': creds['SecretAccessKey'],
        'token': creds['SessionToken'],
        'expiry_time': creds['Expiration'].isoformat()
    }

def get_boto3_session():
    """
    Returns a standard boto3 Session that automatically refreshes its own 
    credentials in the background using the STS assume_role function before 
    they expire. This solves the 1-hour limitation of Role Chaining.
    """
    refreshable_credentials = RefreshableCredentials.create_from_metadata(
        metadata=_fetch_credentials(),
        refresh_using=_fetch_credentials,
        method='sts-assume-role'
    )
    
    botocore_session = get_session()
    botocore_session._credentials = refreshable_credentials
    botocore_session.set_config_variable("region", DEFAULT_REGION)
    
    return boto3.Session(botocore_session=botocore_session)

def client(service_name, **kwargs):
    """
    Returns a boto3 client (e.g., 's3') equipped with auto-refreshing credentials.
    """
    session = get_boto3_session()
    return session.client(service_name, **kwargs)

def resource(service_name, **kwargs):
    """
    Returns a boto3 resource equipped with auto-refreshing credentials.
    """
    session = get_boto3_session()
    return session.resource(service_name, **kwargs)
