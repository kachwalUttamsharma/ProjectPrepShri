# Week 4 Cheatsheet - Networking

| Service | One-liner | Typical use |
|---|---|---|
| VPC | Private network in a region | Isolate workloads |
| Subnet | CIDR slice in one AZ | Public/private tiers |
| Route table | Rules choosing next hop | IGW/NAT/TGW routing |
| Internet Gateway | Two-way internet (free) | Public subnets |
| NAT Gateway | Outbound-only internet, per AZ, $$ | Private subnet egress |
| Security group | Stateful allow-only, ENI-level | Primary firewall |
| NACL | Stateless allow/deny, subnet-level | Coarse deny rules |
| Gateway endpoint | Free private path to S3/DynamoDB | Avoid NAT charges |
| Interface endpoint / PrivateLink | ENI to AWS/3rd-party/own services | Private service access |
| VPC peering | 1:1, non-transitive | Few VPCs |
| Transit Gateway | Regional hub-spoke router | Many VPCs + on-prem |
| Site-to-Site VPN | IPsec over internet, 2 tunnels | Quick hybrid / DX backup |
| Direct Connect | Dedicated private link 1-100 Gbps | Steady hybrid, low latency |
| Route 53 | DNS + health checks + routing policies | Failover, latency, weighted |
| CloudFront | CDN with edge caching, WAF, OAC | Static + dynamic acceleration |
| Global Accelerator | Anycast static IPs over AWS backbone | TCP/UDP global failover |
| Flow Logs / Reachability Analyzer | Traffic metadata / path analysis | Connectivity debugging |
| ELB (ALB/NLB/GWLB) | Load balancing L7/L4/appliance | Entry points |
| Network Firewall | Managed stateful firewall (VPC) | Egress filtering, IDS/IPS |

Numbers: AWS reserves 5 IPs/subnet; VPC CIDR /16-/28; 5 VPCs/region default; VPN tunnel ~1.25 Gbps, 2 tunnels; DX 1/10/100 Gbps; CloudFront ACM cert in us-east-1.
Routing policies: simple, weighted, latency, failover, geolocation, geoproximity, multivalue, IP-based.
Remember: SG = stateful allow; NACL = stateless allow/deny; peering non-transitive; NAT per AZ; endpoints save NAT cost.
