import os
import json
import urllib.request
import urllib.error
import socket

def get_user():
    """
    Retrieves the user identity dynamically.
    First checks environment variables for manual overrides or injected values.
    If not found, queries the Kubernetes API for the pod's opendatahub.io/username annotation.
    """
    user = os.getenv("RHOAI_USER")
    if user:
        return user
        
    user = os.getenv("JUPYTERHUB_USER")
    if user:
        return user

    # Attempt to read from Kubernetes API
    try:
        # Get pod namespace
        with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace", "r") as f:
            namespace = f.read().strip()
            
        # Get pod token
        with open("/var/run/secrets/kubernetes.io/serviceaccount/token", "r") as f:
            token = f.read().strip()
            
        # Get pod name
        pod_name = socket.gethostname()
        
        # Build API request
        url = f"https://kubernetes.default.svc/api/v1/namespaces/{namespace}/pods/{pod_name}"
        headers = {"Authorization": f"Bearer {token}"}
        
        req = urllib.request.Request(url, headers=headers)
        
        # Disable SSL verification for the internal cluster CA
        import ssl
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(req, context=context) as response:
            data = json.loads(response.read().decode())
            
            # Check annotations for username (RHODS standard)
            annotations = data.get("metadata", {}).get("annotations", {})
            if "opendatahub.io/username" in annotations:
                return annotations["opendatahub.io/username"]
            
            # Fallback to checking labels just in case
            labels = data.get("metadata", {}).get("labels", {})
            if "opendatahub.io/user" in labels:
                return labels["opendatahub.io/user"]
                
    except Exception as e:
        print(f"Failed to fetch user from Kubernetes API: {e}")
        pass
        
    return "unknown_user"
