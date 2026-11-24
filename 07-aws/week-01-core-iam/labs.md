# Week 1 Labs (OPTIONAL, free-tier friendly)

COST WARNING: IAM/Organizations/Budgets are free. Do not create paid resources in this week. Use a personal account, never a work account.

1. Secure the root: enable MFA on root, create an admin via IAM Identity Center (or an IAM user with MFA if Identity Center is unavailable), stop using root.
2. Budget: Billing > Budgets > create a zero-spend or $5 budget with email alert.
3. Least privilege: create a role `StudyReadS3` with a custom policy allowing only `s3:ListBucket` on one bucket ARN; use the IAM Policy Simulator to test allowed/denied actions.
4. Assume role: create a role trusting your user; run `aws sts assume-role ...` then `aws sts get-caller-identity` with the temporary env vars.
5. Read the credential report (IAM > Credential report) and Access Analyzer findings.

Cleanup: delete test roles/users/policies; keep the budget (it is free).
