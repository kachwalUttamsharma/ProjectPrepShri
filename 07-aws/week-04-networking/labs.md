# Week 4 Labs (OPTIONAL)

COST WARNING: VPC, subnets, route tables, IGW, SGs, NACLs and gateway endpoints are free. NAT Gateway (~hourly + per GB), interface endpoints, Transit Gateway, VPN, ALB, and public IPv4 addresses are NOT free. Create the NAT Gateway only for a short test and delete it immediately; release Elastic IPs.

1. Build a VPC by hand: 2 public + 2 private subnets in 2 AZs, IGW, route tables. Compare to the "VPC and more" wizard.
2. Launch a t-class instance in a public subnet with an SG allowing nothing inbound; use Session Manager. Then try adding/removing SG rules and NACL deny rules to observe stateful vs stateless behavior.
3. Add an S3 gateway endpoint and confirm a private instance can reach S3 without NAT.
4. Route 53 (only if you own a domain, ~$0.50/zone/month): create weighted records.
5. CloudFront in front of a private S3 bucket with OAC (free-tier traffic is small).
6. Turn on VPC Flow Logs to S3 for a few minutes; read REJECT lines.

Cleanup: delete NAT gateway then release its EIP, delete endpoints, terminate instances, delete VPC (dependency order: instances, endpoints, NAT, IGW detach/delete, subnets, route tables, SGs, VPC), delete CloudFront distributions (disable first), hosted zones, Flow Log S3 data.
