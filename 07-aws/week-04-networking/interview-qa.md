# Week 4 Interview Q&A - Networking

**1. What makes a subnet public vs private?**
Route table: public has 0.0.0.0/0 -> Internet Gateway (and resources need public/Elastic IPs). Private has no IGW route; outbound goes through NAT Gateway or endpoints.

**2. Security group vs NACL?**
SG: instance/ENI level, stateful, allow rules only, can reference other SGs. NACL: subnet level, stateless, allow and deny, numbered rules evaluated in order. Use SGs primarily; NACLs for explicit denies/coarse guardrails.

**3. What does "stateful" mean here?**
If inbound is allowed, the response is automatically allowed regardless of outbound rules. NACLs need explicit rules for return traffic (ephemeral ports).

**4. IGW vs NAT Gateway?**
IGW enables two-way internet for resources with public IPs; free. NAT Gateway lets private resources initiate outbound connections only; hourly + per-GB cost, zonal, sits in a public subnet.

**5. NAT Gateway bill is huge. Why and what do you do?**
Per-GB processing charges, often from S3/DynamoDB/ECR/CloudWatch traffic. Add S3/DynamoDB gateway endpoints (free) and interface endpoints for heavy services, consolidate cross-AZ routing (one NAT per AZ to avoid cross-AZ charges), review with Flow Logs / Cost Explorer.

**6. Gateway endpoint vs interface endpoint?**
Gateway: S3 and DynamoDB only, route-table based, free. Interface (PrivateLink): ENI with private IP, works for most services and custom/third-party services, hourly + data charges, uses DNS and SGs.

**7. What is PrivateLink and when do you use it?**
Exposes a service (behind an NLB/GWLB) to consumers' VPCs privately via endpoints, one direction, no CIDR coordination or peering. Ideal for SaaS vendors and shared-services across accounts.

**8. VPC Peering vs Transit Gateway?**
Peering: simple 1:1, no transitive routing, no overlapping CIDRs, cheap (only transfer). TGW: hub-and-spoke, transitive routing, scales to many VPCs and on-prem, route table segmentation, per-attachment + per-GB cost. Use peering for a few VPCs, TGW for many.

**9. Scenario: two VPCs with overlapping CIDRs must share one API. Option?**
PrivateLink (NLB-fronted service + interface endpoint) since it doesn't require routing between CIDRs. Peering/TGW can't connect overlapping CIDRs without NAT tricks.

**10. VPN vs Direct Connect?**
VPN: encrypted IPsec over internet, quick (minutes), up to ~1.25 Gbps per tunnel, variable latency, cheap. DX: dedicated private link, 1-100 Gbps, consistent latency, lower transfer cost, weeks to provision, not encrypted by default. Best practice: DX primary with VPN backup, or two DX locations.

**11. Route 53 routing policies: list and give use cases.**
Simple, Weighted (canary/blue-green), Latency (multi-region performance), Failover (active-passive), Geolocation (compliance/localization), Geoproximity (shift traffic by distance bias), Multivalue (basic client-side LB with health checks), IP-based (route by client CIDR/ISP).

**12. Alias vs CNAME?**
Alias is Route 53-specific, works at zone apex, free for AWS targets, resolves to A/AAAA directly and tracks target health. CNAME cannot be used at apex and queries are billed.

**13. Scenario: active-passive DR with DNS failover.**
Primary and secondary alias records with failover policy, health check on primary (endpoint or CloudWatch alarm), low TTL (e.g. 60 s). Note clients/resolvers cache; for faster failover use Global Accelerator or ARC.

**14. How does CloudFront work and what are its benefits?**
Requests route to nearest edge; cache hit returns directly, miss goes via regional edge cache to origin. Benefits: lower latency, reduced origin load, DDoS absorption (Shield), WAF at edge, cheaper egress, TLS termination close to user.

**15. How do you serve a private S3 bucket via CloudFront?**
Origin Access Control (OAC) with a bucket policy allowing only the CloudFront distribution (service principal + `AWS:SourceArn`); Block Public Access stays on. Use signed URLs/cookies for authorized content.

**16. CloudFront Functions vs Lambda@Edge?**
CloudFront Functions: lightweight JS, sub-millisecond, viewer events only, cheap (header rewrites, redirects, simple auth tokens). Lambda@Edge: full Lambda (Node/Python), longer duration, network access, origin and viewer events; use for heavier logic.

**17. CloudFront vs Global Accelerator?**
CloudFront caches HTTP content at edge. Global Accelerator provides static anycast IPs and routes any TCP/UDP traffic over the AWS backbone to the best healthy regional endpoint with fast failover; no caching.

**18. Scenario: private EC2 can't reach the internet to download packages.**
Check: route 0.0.0.0/0 -> NAT Gateway in a public subnet in the same AZ; NAT has an Elastic IP and its subnet routes to IGW; SG/NACL egress; DNS. Alternatively use VPC endpoints / package mirror.

**19. Troubleshooting: Fargate task in private subnet can't pull ECR image.**
Needs a path: NAT or VPC endpoints for ecr.api, ecr.dkr, S3 gateway endpoint, and logs endpoint; SG on interface endpoints must allow 443 from task SG; private DNS enabled; execution role permissions.

**20. How do you design a 3-tier VPC for HA?**
2-3 AZs; per AZ: public subnet (ALB, NAT), private app subnet, isolated data subnet. Routes: public->IGW, app->NAT, data->no internet. SG chaining; Multi-AZ RDS; endpoints for AWS services; Flow Logs; plan non-overlapping CIDR with room to grow.

**21. How many IPs are usable in a /24 subnet?**
256 - 5 reserved by AWS = 251.

**22. VPC peering is non-transitive. What does that mean?**
If A peers with B and B peers with C, A cannot reach C through B. Need direct A-C peering or TGW.

**23. What are VPC Flow Logs good for?**
Metadata of accepted/rejected flows at VPC/subnet/ENI level to CloudWatch/S3. Debug connectivity (REJECT entries), detect anomalies, audit. They don't capture payloads; for that use Traffic Mirroring.

**24. Security angle: how to restrict an ALB to only accept traffic from CloudFront?**
Allow the CloudFront managed prefix list in the ALB SG, and add a secret custom header from CloudFront verified at the ALB/WAF rule. Also keep WAF at CloudFront.

**25. Cost angle: data transfer pitfalls.**
Internet egress, cross-AZ (both directions charged), cross-region, NAT processing, public IPv4 hourly, TGW per-GB. Prefer same-AZ traffic where it doesn't hurt HA, CloudFront for egress, endpoints, compress, and cache.

**26. How do you connect on-prem to many VPCs?**
Direct Connect (or VPN) to a Transit Gateway via Direct Connect Gateway / VPN attachment; route tables per attachment for segmentation; BGP route propagation.
