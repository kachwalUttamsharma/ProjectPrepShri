# Week 4 - Networking

---
## 1. VPC fundamentals

A VPC is your private, logically isolated virtual network in ONE region, spanning all AZs of that region. You pick an IPv4 CIDR (/16 to /28; e.g. 10.0.0.0/16), optional IPv6.

```
 Region
 +--------------------------- VPC 10.0.0.0/16 ----------------------------+
 |  AZ-a                                  AZ-b                            |
 |  [public 10.0.0.0/24]  <-- IGW -->     [public 10.0.1.0/24]            |
 |     ALB, NAT GW                           ALB, NAT GW                  |
 |  [private-app 10.0.10.0/24]            [private-app 10.0.11.0/24]      |
 |     ECS/EC2 -> NAT GW (egress)            ECS/EC2                      |
 |  [private-data 10.0.20.0/24]           [private-data 10.0.21.0/24]     |
 |     RDS primary                           RDS standby                  |
 +------------------------------------------------------------------------+
```

- **Subnet:** CIDR slice within ONE AZ. "Public" = its route table has 0.0.0.0/0 -> Internet Gateway (and instances have public/Elastic IP). "Private" = no direct IGW route.
- AWS reserves 5 IPs per subnet (first 4 + last). /28 -> 11 usable.
- **Route table:** per-subnet rules, longest prefix match; `local` route always present for VPC CIDR. Main vs custom route tables.
- **Internet Gateway (IGW):** horizontally scaled, free, two-way internet for resources with public IPs. IPv6 outbound-only equivalent: Egress-only IGW.
- **NAT Gateway:** managed outbound-only internet for private subnets; lives in a PUBLIC subnet, per AZ (zonal; make one per AZ for HA); ~$0.045/hr + $0.045/GB processed (region-dependent; check docs) -> frequent bill surprise. Up to 100 Gbps scaling. Alternative: NAT instance (cheap, self-managed). Reduce cost with VPC endpoints (S3/DynamoDB gateway endpoints are free).
- Public IPv4 addresses are charged hourly (since Feb 2024), even attached ones; plan for IPv6 / fewer public IPs.
- **Default VPC** in each region: public subnets, convenient but not for production.
- Defaults (soft): 5 VPCs per region, 200 subnets/VPC, 5 CIDR blocks/VPC (check docs).
- **DNS:** enable DNS hostnames/resolution; Route 53 Resolver at base+2 (10.0.0.2); private hosted zones.
- **VPC Flow Logs:** metadata of traffic (accept/reject) to CloudWatch/S3/Firehose; for troubleshooting and security. Reachability Analyzer: static path analysis.

### Security groups vs NACLs (top interview question)
| | Security Group | Network ACL |
|---|---|---|
| Level | ENI/instance | Subnet |
| State | Stateful (return traffic auto-allowed) | Stateless (need ephemeral port rules both ways) |
| Rules | Allow only | Allow and Deny, numbered, first match wins |
| Default | Deny all in, allow all out | Default NACL allows all |
| Reference | Can reference other SGs | CIDR only |
Pattern: SG chaining: `alb-sg` -> `app-sg` (source = alb-sg) -> `db-sg` (source = app-sg, port 5432). Use NACL only for explicit subnet-level deny (block an IP range).

### VPC endpoints
- Gateway endpoints: S3 and DynamoDB only; free; added as route-table entry (prefix list); endpoint policies.
- Interface endpoints (AWS PrivateLink): ENI with private IP in your subnet for most AWS services (ECR, Secrets Manager, CloudWatch Logs, Bedrock, SQS...) or third-party/your own services; hourly per AZ + per GB.
- Gateway Load Balancer endpoints for appliances.
- Use to keep traffic off the internet and avoid NAT charges.

---
## 2. Connecting VPCs and networks
| Option | What | Notes |
|---|---|---|
| VPC Peering | 1:1 private connection between two VPCs (cross-account/region ok) | Non-transitive; no overlapping CIDRs; N*(N-1)/2 meshes don't scale; no edge-to-edge routing |
| Transit Gateway (TGW) | Regional hub-and-spoke router for VPCs, VPN, Direct Connect | Transitive routing, route tables for segmentation, inter-region peering; per-attachment hourly + per-GB; up to 5,000 attachments (check docs) |
| PrivateLink | Expose ONE service (NLB-backed) privately to consumers' VPCs | No CIDR overlap issue, one-directional, SaaS-style |
| Site-to-Site VPN | IPsec over internet; 2 tunnels per connection; ~1.25 Gbps per tunnel | Fast to set up, encrypted, variable latency; BGP or static |
| Direct Connect (DX) | Dedicated private fiber (1/10/100 Gbps; hosted 50 Mbps-25 Gbps) via DX location | Consistent latency, lower egress rates, weeks to provision; NOT encrypted by default (add MACsec / VPN over DX); use 2 locations for resiliency; DX Gateway to reach multiple VPCs/regions |
| Client VPN | Remote user VPN | OpenVPN based |
| Cloud WAN | Managed global network | Global TGW-like |
Choose: few VPCs -> peering; many VPCs/hybrid -> TGW; expose a service to many customers/accounts with overlapping IPs -> PrivateLink; quick hybrid -> VPN; steady high bandwidth/latency-sensitive -> DX (+VPN as backup).

---
## 3. Route 53

DNS service (also domain registration, health checks); 100% availability SLA for DNS data plane. Global.
- Record types: A, AAAA, CNAME, MX, TXT, NS, SRV, CAA...; **Alias** record: Route 53-specific, maps name (including zone apex) to AWS resources (ALB, CloudFront, S3 website, API GW, etc.), free queries, health-aware. CNAME cannot be at zone apex.
- Hosted zones: public vs private (associated with VPCs).
- **Routing policies:**
  - Simple: one or multiple values (random).
  - Weighted: split by weights (canary, A/B).
  - Latency-based: lowest latency region.
  - Failover: active-passive with health checks.
  - Geolocation: by user's country/continent (compliance, localization); needs default.
  - Geoproximity: by distance with bias (Traffic Flow).
  - Multivalue answer: up to 8 healthy records (poor-man's LB).
  - IP-based: by client CIDR.
- Health checks: endpoint, calculated, CloudWatch alarm; can be tied to failover/weighted/latency.
- TTL trade-off: low TTL = faster failover, more queries. Resolver caches can ignore.
- Route 53 Resolver endpoints (inbound/outbound) for hybrid DNS. Application Recovery Controller (ARC) for DR routing control.
- Pricing: per hosted zone/month + per million queries (alias to AWS resources free) + health checks.

---
## 4. CloudFront (CDN) and Global Accelerator
- Global CDN with ~600+ edge locations/PoPs and regional edge caches (check docs). Origins: S3, ALB/EC2, API Gateway, custom HTTP.
- Behaviors: path-pattern -> origin + cache policy + origin request policy. TTL via Cache-Control or defaults. Invalidations (first 1,000 paths/month free, then paid; prefer versioned file names).
- Security: HTTPS via ACM cert (must be in us-east-1 for CloudFront), **OAC (Origin Access Control)** so S3 bucket stays private (replaces OAI), signed URLs/cookies for private content, field-level encryption, geo restriction, AWS WAF + Shield Standard integration.
- Compute at the edge: CloudFront Functions (lightweight JS, sub-ms, viewer req/resp) vs Lambda@Edge (heavier, more runtime/time, 4 regions of origin events too).
- Also: origin failover groups, streaming, HTTP/3, response compression, real-time logs, free tier (1 TB/mo out always-free; check docs). Data transfer out from CloudFront is cheaper than direct from S3/EC2, and origin->CloudFront is free for AWS origins.
- **Global Accelerator:** 2 static anycast IPs, routes TCP/UDP over AWS backbone to nearest healthy regional endpoint (ALB/NLB/EC2/EIP); fast failover (no DNS TTL). Use for non-HTTP, gaming, static IPs, multi-region active-active. CloudFront = caching content; GA = network path optimization, no caching.

---
## 5. Putting it together: secure web app network
```
 User -> Route 53 (alias) -> CloudFront (+WAF) -> ALB (public subnets, 2 AZs)
                                                    |  SG: 443 from CloudFront prefix list
                                                    v
                                     ECS Fargate tasks (private-app subnets)  --NAT--> external APIs
                                          | VPC endpoints: S3(gw), ECR, Logs, Secrets, Bedrock (interface)
                                          v
                                     RDS (private-data subnets, no route to internet)
```

## 6. Troubleshooting checklist ("can't connect")
1. Is there a route? (route table: IGW/NAT/TGW/peering) 2. Public IP/EIP for IGW traffic? 3. SG inbound on target AND outbound on source. 4. NACL both directions incl. ephemeral ports 1024-65535. 5. OS firewall/app listening on 0.0.0.0? 6. DNS resolving (private zone association, enableDnsSupport)? 7. Overlapping CIDRs? 8. Check Flow Logs (REJECT) and Reachability Analyzer. 9. Peering/TGW route entries on BOTH sides. 10. Endpoint policy / bucket policy `aws:SourceVpce`.

## 7. boto3 illustration
```python
ec2 = boto3.client("ec2")
vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")["Vpc"]["VpcId"]          # costs nothing, but clean up
subnet = ec2.create_subnet(VpcId=vpc, CidrBlock="10.0.1.0/24", AvailabilityZone="us-east-1a")
```
