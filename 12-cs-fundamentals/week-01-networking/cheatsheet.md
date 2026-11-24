# Week 1 - Networking Cheatsheet

Facts marked "(check current docs)" are version-dependent.

---
## Layers

| Layer | Unit | Examples | One-liner |
|---|---|---|---|
| L7 Application | message | HTTP, DNS, gRPC | what apps speak |
| (TLS) | records | TLS 1.3 | encrypt + authenticate, above TCP |
| L4 Transport | segment | TCP, UDP, QUIC | ports, reliability, flow/congestion |
| L3 Network | packet | IP, ICMP | end-to-end addressing, routers |
| L2 Link | frame | Ethernet, Wi-Fi, ARP | per-hop delivery by MAC, switches |
| L1 Physical | bits | cable, radio | signals |

## Subnet math

| Prefix | Mask | Addresses | Usable (classic) |
|---|---|---|---|
| /32 | 255.255.255.255 | 1 | host route |
| /30 | 255.255.255.252 | 4 | 2 |
| /28 | 255.255.255.240 | 16 | 14 |
| /26 | 255.255.255.192 | 64 | 62 |
| /24 | 255.255.255.0 | 256 | 254 |
| /22 | 255.255.252.0 | 1,024 | 1,022 |
| /20 | 255.255.240.0 | 4,096 | 4,094 |
| /16 | 255.255.0.0 | 65,536 | 65,534 |

- Addresses = 2^(32-N); block size in the interesting octet = 256 - mask octet.
- Network = floor(octet / block) * block. Example: 172.16.37.200/20 -> 172.16.32.0, broadcast 172.16.47.255.
- Cloud subnets reserve extra addresses (AWS: 5; check current docs).
- Private: 10/8, 172.16/12, 192.168/16. Loopback 127/8. Link-local 169.254/16. CGNAT 100.64/10.
- Longest prefix wins in routing.

## TCP vs UDP

| Topic | One-liner |
|---|---|
| Handshake | SYN, SYN-ACK, ACK = 1 RTT |
| Teardown | FIN/ACK each way; closer enters TIME_WAIT (~2 MSL, 60s Linux) |
| TIME_WAIT pile | pool connections; widen port range; do not disable |
| CLOSE_WAIT pile | app bug: not calling close() |
| RST | abrupt abort: closed port, crash, firewall, idle timeout |
| Flow control | receiver window (rwnd) protects receiver |
| Congestion control | cwnd protects network; in flight <= min(rwnd, cwnd) |
| Slow start | cwnd doubles per RTT (initial ~10 segments; check current docs) |
| Congestion avoidance | +1 MSS per RTT; loss -> halve (timeout -> reset harder) |
| Fast retransmit | 3 duplicate ACKs, no timeout wait |
| BDP | bandwidth x RTT = bytes needed in flight |
| Nagle / delayed ACK | latency trap; use TCP_NODELAY |
| UDP | no handshake/ordering/CC; DNS, QUIC, RTP, DHCP |

## DNS

| Record | Meaning |
|---|---|
| A / AAAA | name -> IPv4 / IPv6 |
| CNAME | alias; not at apex |
| NS | zone delegation |
| MX | mail servers (priority) |
| TXT | SPF, DKIM, verification |
| SRV | host + port |
| PTR | reverse lookup |
| SOA | zone metadata, negative TTL |
| CAA | allowed cert issuers |

- Path: stub -> recursive -> root -> TLD -> authoritative; cached by TTL at every level.
- Status: NOERROR, NXDOMAIN (no such name), SERVFAIL (resolver failure/DNSSEC), REFUSED (ACL).
- Before migrations: lower TTL ahead of time; negative answers are cached too.
- dig bypasses the OS resolver; curl/ping use it (/etc/hosts, search domains).

## HTTP versions

| | 1.1 | 2 | 3 |
|---|---|---|---|
| Transport | TCP | TCP | QUIC over UDP |
| Multiplexing | no | yes | yes |
| HOL blocking | HTTP + TCP | TCP-level | none across streams |
| Compression | none | HPACK | QPACK |
| Setup | TCP + TLS | TCP + TLS | combined, 1 RTT (0-RTT possible) |

- Negotiation: ALPN "h2"; HTTP/3 via Alt-Svc / HTTPS records; fall back when UDP/443 blocked.

## TLS and certs

| Topic | One-liner |
|---|---|
| TLS 1.3 | 1-RTT handshake, forward secrecy, weak ciphers removed |
| 0-RTT | replayable; idempotent requests only |
| Chain | leaf -> intermediate -> root (server sends leaf + intermediates) |
| SAN | holds the valid hostnames; CN is legacy |
| Wildcard | one label only |
| SNI | hostname in ClientHello to pick cert |
| mTLS | client also presents cert |
| Verify error 20 | missing intermediate or untrusted root |
| Public cert lifetimes | shrinking toward ~47 days (check current docs) |

## HTTP status, methods, caching

| Code | Meaning |
|---|---|
| 200 / 201 / 202 / 204 | OK / Created / Accepted / No Content |
| 301/308 vs 302/307 | permanent vs temporary redirect (307/308 keep method) |
| 304 | Not Modified (conditional GET) |
| 400 / 422 | malformed / validation failed (FastAPI default 422) |
| 401 / 403 | unauthenticated / forbidden |
| 404 / 405 / 409 | not found / method not allowed / conflict |
| 429 | rate limited (Retry-After) |
| 500 / 502 / 503 / 504 | app error / bad upstream / unavailable / upstream timeout |

| Method | Safe | Idempotent |
|---|---|---|
| GET HEAD OPTIONS | yes | yes |
| PUT DELETE | no | yes |
| POST | no | no |
| PATCH | no | not guaranteed |

| Cache header | Meaning |
|---|---|
| max-age / s-maxage | fresh seconds (browser / shared cache) |
| no-cache | store but revalidate every time |
| no-store | never store |
| private / public | browser-only / shareable |
| ETag + If-None-Match | validator -> 304 |
| Vary | which request headers key the cache |

## CORS and auth

| Topic | One-liner |
|---|---|
| Origin | scheme + host + port |
| CORS | browser-enforced; curl ignores it |
| Preflight | OPTIONS before non-simple requests (PUT/DELETE, JSON, Authorization) |
| Credentials | need Allow-Credentials + explicit origin (not *) |
| HttpOnly | JS cannot read cookie |
| Secure | HTTPS only |
| SameSite | Strict / Lax (default in browsers) / None+Secure |
| JWT | header.payload.signature; encoded not encrypted |
| JWT checks | signature, exp, iss, aud, pinned alg |
| Session vs JWT | revocable + store vs stateless + hard to revoke |
| CSRF / XSS | cookie auto-attach / injected script |

## Real-time

| Option | Direction | Notes |
|---|---|---|
| Short polling | client pull | simple, wasteful |
| Long polling | client pull, held | works everywhere |
| SSE | server -> client | text/event-stream, auto-reconnect, disable proxy buffering |
| WebSocket | both | HTTP Upgrade (101), needs heartbeats, sticky/pub-sub to scale |

## Debug symptoms

| Symptom | Likely meaning |
|---|---|
| Connection refused (fast) | host reachable, nothing listening / REJECT |
| Timeout (slow) | packets dropped: firewall, SG, route, down host |
| Connection reset | RST: proxy idle timeout, crash, wrong protocol |
| Works on localhost only | bound to 127.0.0.1 |
| Small requests OK, big hang | MTU / PMTU black hole |
| Hangs after N min idle | NAT/LB idle timeout; use keepalive |
| Sporadic 502 after idle | app keep-alive shorter than LB idle timeout |
| dig works, curl fails | OS resolver, hosts file, proxy env |

---
## Key commands

```
dig example.com +short | dig +trace example.com | dig @8.8.8.8 example.com MX | dig -x IP
nslookup example.com
curl -v URL
curl -sS -o /dev/null -w 'dns=%{time_namelookup} tcp=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total}\n' URL
curl --resolve host:443:IP https://host/        # bypass DNS, keep SNI
curl -4 / -6 | curl --http2 / --http1.1 | curl -N (streaming) | curl -L -I
nc -vz host 443                                 # TCP port check
openssl s_client -connect host:443 -servername host -showcerts
openssl x509 -noout -dates -subject -ext subjectAltName
ss -ltnp  (Linux)       lsof -iTCP -sTCP:LISTEN -P -n  (macOS/Linux)       netstat -rn
lsof -i :8000
ss -s | netstat -an | awk '/tcp/ {print $NF}' | sort | uniq -c
traceroute -n host | mtr -rwc 20 host
sudo tcpdump -i any -nn 'host IP and port 443' -c 20
ping -D -s 1472 host    (macOS DF)     ping -M do -s 1472 host  (Linux)
uvicorn app:app --host 0.0.0.0 --port 8000 --proxy-headers
```

## Memorize

- Debug bottom-up: DNS -> route/ping -> TCP connect -> TLS -> HTTP -> app. Stop at first failing rung.
- Refused = RST came back (nobody listening). Timeout = silence (dropped).
- ~4 RTTs cold (DNS + TCP + TLS + request); keep-alive, TLS 1.3, HTTP/3, CDN cut them.
- TIME_WAIT is normal; CLOSE_WAIT is a leak.
- h2 fixes HTTP-level HOL; QUIC fixes TCP-level HOL.
- TLS 1.3 = 1 RTT, forward secrecy; cert chain: send leaf + intermediates, not root.
- 401 = who are you; 403 = not allowed; 502 = bad upstream; 504 = upstream slow.
- CORS is browser-only; preflight is OPTIONS; no `*` with credentials.
- JWT payload is readable by anyone; validate sig, exp, iss, aud, alg.
- Set connect AND read timeouts; retry only idempotent requests, with backoff + jitter.
- Never use `-k` / `verify=False` as a fix.
- Overlapping CIDRs block peering/VPN; ask the customer for ranges up front.
- Capture timestamps, IP:port, request IDs, and command output when escalating.
