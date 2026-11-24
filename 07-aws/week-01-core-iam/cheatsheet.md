# Week 1 Cheatsheet

| Service / concept | One-liner | Typical use |
|---|---|---|
| Region | Isolated geographic area | Data residency, latency, DR |
| AZ | Independent data center group in a region | Multi-AZ HA |
| Edge location | CDN/DNS PoP | CloudFront, Route 53, Global Accelerator |
| Local Zone / Wavelength / Outposts | Region extension / 5G edge / AWS rack on-prem | Low latency in cities / telco / hybrid |
| IAM | Global authN/authZ, free | Control who can do what |
| User / Group / Role | Long-lived identity / user set / assumable temp identity | Humans (prefer SSO) / policy mgmt / services and cross-account |
| Policy (JSON) | Allow/Deny Actions on Resources with Conditions | Permissions |
| Trust policy | Who may assume a role | Cross-account, service roles |
| STS | Issues temporary credentials | AssumeRole, web identity, whoami (GetCallerIdentity) |
| Permissions boundary | Max permission cap on identity | Safe delegation |
| SCP | Org guardrail, never grants | Region/service restrictions |
| IAM Identity Center | Workforce SSO to accounts | Human access |
| Access Analyzer | Finds external/unused access, generates policies | Least privilege |
| Organizations | Account tree, consolidated billing, SCPs | Multi-account governance |
| Control Tower | Landing zone + guardrails + account factory | Quick compliant multi-account setup |
| Cost Explorer / Budgets / CUR | Analyze / alert / detailed billing data | FinOps |
| Trusted Advisor | Best-practice checks | Cost, security, limits |
| AWS Artifact | Compliance reports on demand | Audits |

Memorize
- Eval: default deny -> explicit deny wins -> need allow; SCP/boundary/session must also allow.
- Shared responsibility: AWS = OF the cloud; you = IN the cloud.
- AssumeRole creds: 15m-12h, default 1h, chaining 1h.
- Data in free; data out/cross-AZ/cross-region cost money.
- Use roles not keys; MFA on root; Identity Center for humans.
