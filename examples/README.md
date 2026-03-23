# Example Manifests

These are reference IAM policies and Kubernetes manifests for setting up the dynamic role assumption architecture. All files use placeholder values that you need to replace with your own environment.

## Variables to Replace

| Placeholder | Description | Example |
| --- | --- | --- |
| `123456789012` | Your AWS account ID | `111222333444` |
| `<cluster-oidc-issuer>` | The OIDC issuer URL for your OpenShift cluster (without `https://`). For ROSA/EKS this is provided natively. For self-managed clusters, this is the S3-hosted discovery endpoint. | `rh-dynamic-role-oidc.s3.us-east-8.amazonaws.com` |
| `<data-science-project>` | The OpenShift namespace where your data science workbenches run | `my-ds-project` |
| `OpenShiftAIBaseRole` | The name of your Base IAM Role (IRSA, zero permissions) | `OpenShiftAIBaseRole` |
| `DataScienceTargetRole` | The name of your Target IAM Role (holds actual resource permissions) | `DataScienceTargetRole` |
| `user1`, `user2` | Keycloak / OAuth usernames that will be passed as STS session tags | `alice`, `bob` |
| `rh-dynamic-role-bronze-2`, etc. | S3 bucket names for your data tiers | `my-team-bronze`, `my-team-silver` |
| `rh-dynamic-role-oidc-discovery` | The S3 bucket hosting your OIDC discovery/JWKS documents (self-managed clusters only) | `my-cluster-oidc-bucket` |

## Files

### AWS IAM Policies

| File | Attach To | Purpose |
| --- | --- | --- |
| `irsa-trust-policy.json` | **Base Role** (trust policy) | Allows the OpenShift cluster's OIDC provider to assume the Base Role via `AssumeRoleWithWebIdentity`. Uses `StringLike` with `system:serviceaccount:*:*` so any ServiceAccount in any namespace can assume it. |
| `irsa-base-policy.json` | **Base Role** (permissions policy) | The only permission the Base Role has: `sts:AssumeRole` + `sts:TagSession` on the Target Role. It cannot access any AWS resources directly. |
| `target-trust-policy.json` | **Target Role** (trust policy) | Allows the Base Role to chain into the Target Role via `AssumeRole` with session tags. |
| `target-s3-policy.json` | **Target Role** (permissions policy) | Grants S3 access based on `aws:PrincipalTag/user` session tag. In this example, `user1` gets bronze + silver, `user2` gets diamond. |
| `s3_policy.json` | **OIDC Discovery S3 Bucket** (bucket policy) | Makes the OIDC discovery bucket publicly readable so AWS IAM can fetch `/.well-known/openid-configuration` and `/jwks.json`. Only needed for self-managed clusters. |

### Kubernetes Manifests

| File | Purpose |
| --- | --- |
| `sa.yaml` | ServiceAccount annotated with the Base Role ARN. This is the manual approach -- see `poddefault-irsa.yaml` for the automated alternative. |
| `poddefault-irsa.yaml` | PodDefault that automatically injects `AWS_ROLE_ARN`, `AWS_WEB_IDENTITY_TOKEN_FILE`, and a projected ServiceAccount token into every workbench pod. This is the recommended approach for production. |

## Quick Start

1. Replace all placeholders in the files above with your real values.
2. Create the Base Role in AWS IAM:
   - Trust policy: `irsa-trust-policy.json`
   - Permissions policy: `irsa-base-policy.json`
3. Create the Target Role in AWS IAM:
   - Trust policy: `target-trust-policy.json`
   - Permissions policy: `target-s3-policy.json`
4. Apply the Kubernetes manifests:

```bash
oc apply -f poddefault-irsa.yaml
```

5. Restart any existing workbenches to pick up the injected token.
