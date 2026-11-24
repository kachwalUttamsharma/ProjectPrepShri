# AWS Study Track (interview-focused, ~6 weeks at 7-8 hrs/week)

Goal: AWS fundamentals and interview-level knowledge for forward-deployed-engineer / backend roles. All material is reading + Q&A; labs are optional and may cost money (read the warnings). Numbers that change are marked "check current docs" - verify before quoting.

## Study order
| Week | Folder | Topics |
|---|---|---|
| 1 | week-01-core-iam | Regions/AZs/edge, shared responsibility, IAM, STS, Organizations, billing |
| 2 | week-02-compute | EC2, Lambda, ECS/EKS/Fargate, Beanstalk, ELB, Auto Scaling |
| 3 | week-03-storage-databases | S3, EBS/EFS/FSx, RDS/Aurora, DynamoDB, ElastiCache, Redshift, choosing a DB |
| 4 | week-04-networking | VPC, SG vs NACL, NAT/IGW, endpoints, peering/TGW/PrivateLink, Route 53, CloudFront, VPN/DX |
| 5 | week-05-integration-ops-security | SQS/SNS/EventBridge/Kinesis, Step Functions, API Gateway, CloudWatch/CloudTrail/Config, IaC, KMS, Secrets, Cognito, WAF/Shield |
| 6 | week-06-architecture-fde | Well-Architected, HA/DR, cost, serverless vs containers, FastAPI+RAG walkthrough, scenarios, mock interview |

## Weekly routine (7-8 hrs)
1. Read lesson.md (about 3 hrs); draw each ASCII diagram by hand once.
2. Do interview-qa.md out loud, covering the answer first (about 2 hrs).
3. Memorize cheatsheet.md; flashcard the numbers (1 hr).
4. Optional labs.md (1-2 hrs) - set a budget alarm first, clean up the same day.
5. Last 30 min: restate 5 "X vs Y" differences without notes.

## Files
- week-NN-*/lesson.md, interview-qa.md, cheatsheet.md, labs.md (optional)
- week-06-architecture-fde/scenarios.md (10 system-design scenarios), mock-interview.md
- rapid-fire.md: top-50 quick Q&A; use daily in the last two weeks.

## Tips
- For every service be able to say: what it is, when to use, when not to, alternatives, pricing meter, key limit, common gotcha.
- Always bring security and cost angles unprompted.
- If you can't remember a number, state the order of magnitude and say you'd confirm in the docs.
