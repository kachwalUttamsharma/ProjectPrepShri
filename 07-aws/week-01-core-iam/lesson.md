# Week 1 - Core Ideas: Global Infrastructure, IAM, Shared Responsibility, Organizations

Time budget: ~7-8 hrs. Read lesson (3h), Q&A aloud (2h), cheatsheet + optional labs (2h).
Numbers marked "(check current docs)" change over time; verify before quoting in an interview.

---
## 1. Global infrastructure

```
 AWS Global
 |-- Region (e.g. us-east-1, eu-west-1)  -- isolated geographic area, own services/pricing/quotas
 |     |-- Availability Zone (AZ)        -- one or more discrete data centers, separate power/network/flood plain
 |     |     (AZs in a region are linked by low-latency private fiber; typically 3 or more AZs per region)
 |-- Local Zones   -- extensions of a region closer to cities (latency-sensitive: media, gaming)
 |-- Wavelength    -- compute embedded in telco 5G networks
 |-- Outposts      -- AWS hardware in YOUR data center (hybrid)
 |-- Edge locations / PoPs -- CloudFront, Route 53, WAF, Shield, Global Accelerator (hundreds of sites)
        Regional edge caches sit between edge locations and origin
```

Key points
- Region = unit of data residency, isolation, and compliance. Data does not leave a region unless you move it.
- AZ = unit of high availability. "Multi-AZ" = survive a data-center failure. "Multi-Region" = survive a regional failure / reduce latency globally / DR.
- AZ names (us-east-1a) are mapped per-account (randomized); use AZ IDs (use1-az1) when coordinating across accounts.
- Some services are global (IAM, Route 53, CloudFront, Organizations, WAF for CloudFront); most are regional; EC2/EBS subnets are AZ-scoped.
- Choosing a region: latency to users, compliance/data residency, service availability, price (varies by region; us-east-1 is typically cheapest and gets new services first), DR pairing.
- Opt-in regions must be enabled in the account first.

Gotcha: "I can't see my EC2 instance" -> you are in the wrong region in the console/CLI.

---
## 2. Shared Responsibility Model

```
 CUSTOMER: "security IN the cloud"          AWS: "security OF the cloud"
 +------------------------------------+     +-----------------------------------+
 | Customer data, IAM, app code       |     | Physical data centers, hardware   |
 | OS patching (EC2), firewall (SG)   |     | Hypervisor, host OS (Nitro)       |
 | Encryption choices, network config |     | Global network, managed-service   |
 +------------------------------------+     | internals                         |
                                            +-----------------------------------+
```
- Responsibility shifts with abstraction: EC2 (you patch the OS) -> RDS (AWS patches the DB engine, you manage users/params/security groups/data) -> Lambda/S3 (AWS manages runtime/infrastructure; you manage code, IAM, bucket policies, data).
- "Inherited controls" (physical), "shared controls" (patching, config mgmt, training), "customer-specific controls".
- Interview line: "AWS secures the cloud; I secure what I put in it. Most breaches are misconfiguration - public S3 bucket, over-broad IAM - which are customer-side."
- Compliance: AWS Artifact gives audit reports (SOC, ISO, PCI) on demand.

---
## 3. IAM (Identity and Access Management)

**What:** Global service controlling who (authentication) can do what (authorization) on which AWS resources. Free.

### Building blocks
| Concept | Meaning |
|---|---|
| Root user | Email that created the account. Full power. MFA on, no access keys, use only for the few root-only tasks (close account, change support plan, restore IAM perms, etc.) |
| IAM user | Long-lived identity for a person/app. Prefer SSO/Identity Center for humans; avoid users + access keys. |
| Group | Collection of users; attach policies to groups. Cannot nest groups. Groups are not principals (cannot be named in a resource policy Principal). |
| Role | Identity with permissions but no long-term credentials; assumed by users, services, other accounts, federated identities. Gives temporary credentials via STS. |
| Policy | JSON document of permissions. |
| Permissions boundary | Max-permissions guardrail on a user/role (effective = identity policy AND boundary). |
| SCP | Org-level guardrail on accounts/OUs (does not grant, only limits; does not affect management account). |

### Policy types
1. Identity-based (attach to user/group/role): AWS managed, customer managed, inline.
2. Resource-based (attach to resource: S3 bucket policy, SQS, KMS key policy, Lambda, role trust policy). Has `Principal`.
3. Permissions boundaries. 4. SCPs / RCPs (resource control policies). 5. Session policies (passed at AssumeRole). 6. ACLs (legacy, S3).

### Policy anatomy
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "ReadReportsBucket",
    "Effect": "Allow",
    "Action": ["s3:GetObject", "s3:ListBucket"],
    "Resource": ["arn:aws:s3:::reports", "arn:aws:s3:::reports/*"],
    "Condition": {"IpAddress": {"aws:SourceIp": "203.0.113.0/24"}}
  }]
}
```
Note: `ListBucket` applies to the bucket ARN; `GetObject` to `bucket/*`. Classic gotcha.

### Evaluation logic (memorize)
1. Default = implicit DENY.
2. Explicit DENY anywhere wins over everything.
3. Otherwise need an explicit ALLOW (identity or resource policy).
4. Within the same account, identity policy OR resource policy allow is enough (union) - unless an SCP/boundary/session policy doesn't permit it.
5. Cross-account: need allow on BOTH sides (identity policy in caller account AND resource policy / trust in target), roughly.
6. With Orgs: effective = SCP AND (boundary) AND (session) AND (identity/resource allow).

### Roles, trust, STS
```
 Caller (user / EC2 / Lambda / other account)
      |  sts:AssumeRole  (allowed by role TRUST policy + caller's identity policy)
      v
 STS returns temporary creds: AccessKeyId + SecretAccessKey + SessionToken (expire)
      |
      v  call AWS APIs with role's PERMISSION policy
```
- Role has two policies: trust policy (who can assume) and permissions policy (what it can do).
- AssumeRole session: default 1 hr, 15 min to 12 hr (role max session setting). Role chaining caps at 1 hr.
- Related STS calls: AssumeRoleWithWebIdentity (OIDC, e.g. EKS IRSA, GitHub Actions), AssumeRoleWithSAML, GetSessionToken, GetCallerIdentity (the "whoami", needs no permissions).
- Instance profile = container that passes a role to EC2. Lambda has an execution role. ECS has task role (app permissions) vs task execution role (pull image, write logs, fetch secrets).
- Cross-account: add trust to role in account B for account A principal; use `ExternalId` for third parties (confused deputy).
- IAM Identity Center (successor to AWS SSO): central SSO for humans across accounts, permission sets, short-lived creds. Recommended for workforce.

### Least privilege workflow
Start from managed/starter policy -> use IAM Access Analyzer (policy generation from CloudTrail, unused access findings, external-access findings) -> "last accessed" data -> tighten -> add conditions (`aws:MultiFactorAuthPresent`, `aws:SourceVpce`, `aws:PrincipalOrgID`, tag-based ABAC).

### Limits (check current docs)
Users per account 5,000; groups 300; roles 1,000 (raisable); managed policy size 6,144 characters; inline per user 2,048 chars total; managed policies per role 10 by default (raisable to 20).

### When NOT to use IAM users
Apps on AWS compute (use roles), CI/CD (use OIDC federation to a role), humans (use Identity Center). Static access keys leak.

### Gotchas
- `"Action": "*", "Resource": "*"` is admin; wildcard principals `"Principal": "*"` on resource policy = public.
- Changing a policy is eventually consistent (seconds).
- Deny with `NotAction` is easy to get wrong.
- Credentials precedence in SDK/CLI: explicit params -> env vars -> shared credentials/config profile -> container creds -> instance metadata (IMDSv2). Never hardcode keys.

---
## 4. AWS Organizations, billing basics

- Organizations: group accounts into a tree of OUs under a management (payer) account. Features: consolidated billing (one bill, pooled volume discounts, shared Reserved Instance/Savings Plans), SCPs, centralized CloudTrail, tag policies, backup policies, delegated administrators for security services (GuardDuty, Security Hub, Config).
- Why multi-account? Blast-radius isolation, per-team/env billing, separate quotas, security boundaries. Typical: management, security/log-archive, shared-services/network, workload accounts per env (dev/stage/prod).
- Control Tower: opinionated landing zone setup (guardrails, account vending - Account Factory) on top of Organizations.
- SCPs: deny-list approach (FullAWSAccess + explicit denies, e.g. deny leaving the org, deny non-approved regions, deny disabling CloudTrail). Do not affect the management account or service-linked roles.
- Billing tools: Billing console, Cost Explorer, Budgets (alerts + actions), Cost and Usage Report (CUR/Data Exports - most granular), Cost Allocation Tags (must be activated), Cost Anomaly Detection, Compute Optimizer, Trusted Advisor (checks vary by support plan).
- Free tier types: 12-month free (new accounts historically), always-free (e.g. Lambda 1M requests/mo, DynamoDB 25GB), trials. AWS changed free tier for new accounts in 2025 to a credit-based model - check current docs.
- Support plans: Basic (free), Developer, Business, Enterprise On-Ramp, Enterprise. Differences: response times, TAM, full Trusted Advisor checks.

---
## 5. Core pricing mental model
Compute (time/capacity), storage (GB-month), requests, data transfer. Data IN is free; data OUT to internet is charged; cross-AZ and cross-region transfer charged; same-AZ private IP traffic free. Always ask "what is the meter?"

---
## 6. Architecture example: multi-account landing zone
```
 Management account (billing, Orgs, SCPs only)
   |-- OU Security: log-archive acct (CloudTrail, Config -> S3), audit acct (GuardDuty/SecurityHub admin)
   |-- OU Infrastructure: network acct (Transit Gateway), shared-services
   |-- OU Workloads/Prod: app-a-prod, app-b-prod
   |-- OU Workloads/NonProd: app-a-dev, app-a-stage
   |-- OU Sandbox: dev experiments w/ strict budgets + SCP region deny
 Humans -> IAM Identity Center -> permission set -> role in target account
 CI/CD  -> GitHub OIDC -> AssumeRoleWithWebIdentity -> deploy role
```

## 7. boto3 snippets (illustrative; need credentials to run)
```python
import boto3
sts = boto3.client("sts")
print(sts.get_caller_identity()["Arn"])          # who am I?

# assume a role in another account
creds = sts.assume_role(
    RoleArn="arn:aws:iam::222222222222:role/ReadOnly",
    RoleSessionName="study-session",
    DurationSeconds=3600,
)["Credentials"]
s3 = boto3.client("s3",
    aws_access_key_id=creds["AccessKeyId"],
    aws_secret_access_key=creds["SecretAccessKey"],
    aws_session_token=creds["SessionToken"])
```
Simulate a policy decision: `iam.simulate_principal_policy(...)` or the IAM Policy Simulator in the console.
