# Week 1 Interview Q&A - Core, IAM, Shared Responsibility, Organizations

Practice: answer out loud in 30-60 seconds first, then compare.

**1. What is a Region vs an Availability Zone vs an edge location?**
Region = isolated geographic area with its own services and quotas. AZ = one or more data centers within a region with independent power/network, connected by low-latency links; the HA unit. Edge location = CDN/DNS point of presence used by CloudFront, Route 53, WAF, Global Accelerator to serve users close to them.

**2. How do you choose a region?**
Compliance/data residency first, then latency to users, service availability, price, and DR pairing. Also quota and capacity considerations.

**3. Multi-AZ vs Multi-Region?**
Multi-AZ protects against a data center failure with low latency and synchronous replication options; it is the default for production. Multi-Region protects against regional failure and gives global latency, but costs more, adds replication lag/complexity and data-transfer fees. Use it when RTO/RPO or regulation demands it.

**4. Explain the shared responsibility model.**
AWS is responsible for security OF the cloud (facilities, hardware, hypervisor, managed-service internals). Customer is responsible for security IN the cloud (data, IAM, OS patches on EC2, network config, encryption choices). Responsibility shifts toward AWS with more managed services (EC2 -> RDS -> Lambda/S3).

**5. Who patches the OS on EC2? On RDS? On Lambda?**
EC2: you. RDS: AWS patches OS and engine (you schedule maintenance windows and handle app-level config). Lambda: AWS patches the runtime/OS; you update your dependencies and code.

**6. What is the difference between an IAM user, group, and role?**
User = long-lived identity with credentials. Group = collection of users for attaching policies (not a principal). Role = assumable identity with temporary credentials, no password/keys; used by services, cross-account access, and federation.

**7. Why prefer roles over access keys?**
Temporary, auto-rotated credentials, no secrets to leak or store, scoped by trust policy. Access keys are long-lived and the top cause of credential leaks.

**8. Explain the IAM policy evaluation logic.**
Default deny. Explicit deny always wins. Otherwise an explicit allow is required, and with Organizations/boundaries/session policies the request must also be permitted by each of those layers. Within one account an allow in either identity or resource policy suffices; cross-account needs both sides.

**9. Identity-based vs resource-based policy?**
Identity-based attaches to a principal (user/role) and says what it can do. Resource-based attaches to a resource (S3 bucket, SQS, KMS key, role trust) and names a Principal. Resource-based policies enable cross-account access without assuming a role.

**10. What is a trust policy?**
A resource-based policy on a role defining who may assume it (the Principal and conditions). The role's permission policy defines what it can do after assumption.

**11. How does AssumeRole work and what does STS return?**
Caller (permitted by identity policy and the role's trust policy) calls sts:AssumeRole and gets temporary AccessKeyId, SecretAccessKey and SessionToken, valid 15 min to 12 hours (default 1 hr; role chaining max 1 hr).

**12. Scenario: App in account A needs to read an S3 bucket in account B. Options?**
(a) Bucket policy in B granting A's role principal + identity policy in A; or (b) role in B with trust for A's role; A assumes it. (b) is better when you need many resources or auditing by role; (a) is simpler for a single bucket. Mind bucket-owner and KMS key policy if encrypted with a CMK.

**13. What are permissions boundaries and when would you use them?**
A managed policy setting the maximum permissions an identity can have; effective = identity policy AND boundary. Used to delegate IAM administration safely (developers can create roles but only within the boundary).

**14. SCP vs IAM policy?**
SCP is an Organizations guardrail applied to accounts/OUs that restricts what is allowed but never grants. IAM policies grant. SCPs do not affect the management account or service-linked roles.

**15. Scenario: An EC2 instance needs to write to DynamoDB. How do you give it credentials?**
Create an IAM role with least-privilege DynamoDB permissions and attach via instance profile. SDK picks credentials from IMDSv2 automatically. No keys on disk. Require IMDSv2 to mitigate SSRF credential theft.

**16. How do you grant a CI system (GitHub Actions) deploy access without storing keys?**
OIDC federation: register GitHub as an IAM OIDC identity provider, create a role with trust restricted by `sub`/`aud` claims (repo/branch), workflow calls AssumeRoleWithWebIdentity for short-lived creds.

**17. Troubleshooting: "AccessDenied" calling S3 GetObject though the role policy allows it.**
Check: explicit deny (bucket policy/SCP/boundary), wrong ARN (missing `/*`), bucket policy VPC-endpoint/IP condition, KMS key policy lacking decrypt for the role, object owned by another account, Block Public Access/ACL issues, wrong region/account, session policy. Use CloudTrail error message, IAM Policy Simulator, `sts get-caller-identity` to confirm who you are.

**18. What is least privilege and how do you achieve it in practice?**
Grant only needed actions on needed resources under needed conditions. Start narrow, use Access Analyzer policy generation from CloudTrail, review last-accessed data, use ABAC tags, boundaries, and periodic reviews.

**19. What should you do with the root account?**
Enable MFA (ideally hardware), remove access keys, set a shared mailbox/alias, use it only for root-only tasks, and set alerts on its use.

**20. Why use multiple AWS accounts?**
Isolation (security and blast radius), separate billing and quotas, compliance scoping, per-environment boundaries. Managed with Organizations + Control Tower + SCPs.

**21. What does consolidated billing give you?**
One invoice for all member accounts, pooled usage for volume discounts, and shared RI/Savings Plans benefits.

**22. How would you control cost surprises in a new account?**
Budgets with alerts/actions, Cost Anomaly Detection, enforce tags, SCPs limiting regions/expensive services in sandbox, Cost Explorer review, delete unused resources (NAT gateways, idle load balancers, unattached EBS/Elastic IPs).

**23. What is IAM Identity Center?**
Central workforce SSO across accounts and apps; assigns permission sets that map to roles in each account; issues short-lived credentials; integrates with external IdPs (Okta, Entra).

**24. Which AWS services are global versus regional?**
Global (control plane): IAM, Organizations, Route 53, CloudFront, WAF (for CloudFront), Shield. Most others (EC2, S3 buckets, RDS, Lambda, DynamoDB) are regional; subnets/EBS volumes/instances are AZ-scoped. S3 bucket names are globally unique but data lives in one region.

**25. Security angle: how do you detect an exposed access key?**
CloudTrail + GuardDuty (anomalous API use), AWS auto-flags keys found on public GitHub and attaches quarantine policy, Access Analyzer/credential report for old keys. Response: deactivate key, review CloudTrail for actions, rotate, move to roles.
