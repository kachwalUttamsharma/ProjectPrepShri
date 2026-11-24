# Week 1 - Networking: Layers, IP, TCP/UDP, DNS, HTTP, TLS, Web Auth, Debugging

Time budget: ~7-8 hrs. Read lesson (3h), run the terminal commands (2h), Q&A aloud (2h), cheatsheet (1h).
Facts marked "(check current docs)" are version-dependent (defaults, RFC status, browser behavior); verify before quoting in an interview.

---
## 1. Layered models: OSI vs TCP/IP

Why layers? Each layer solves one problem and hides it from the layer above. Your FastAPI handler never thinks about Ethernet frames.

```
 OSI (7)                 TCP/IP (4)        Unit        Examples
 7 Application  \
 6 Presentation  }-----> Application       message     HTTP, DNS, TLS(ish), SSH, gRPC
 5 Session      /
 4 Transport    -------> Transport         segment/    TCP, UDP, QUIC (over UDP)
                                           datagram
 3 Network      -------> Internet          packet      IP (v4/v6), ICMP, routing
 2 Data link    \
 1 Physical      }-----> Link              frame/bit   Ethernet, Wi-Fi, ARP, MAC addrs
```

Encapsulation (what actually goes on the wire):

```
 App data:            [ HTTP request bytes ]
 + TCP header:      [TCP][ HTTP request bytes ]            (ports, seq, ack, flags)
 + IP header:     [IP][TCP][ HTTP request bytes ]          (src/dst IP, TTL)
 + Ethernet:  [Eth][IP][TCP][ HTTP request bytes ][FCS]    (src/dst MAC, per hop)
```

Key points
- MAC addresses change at every hop (L2 is local). IP addresses stay end-to-end (except NAT).
- Router = L3 device (forwards by destination IP). Switch = L2 (by MAC). Load balancer: L4 (by IP:port, e.g. NLB) or L7 (by HTTP host/path, e.g. ALB, nginx).
- ARP maps IPv4 -> MAC on the local subnet. Off-subnet traffic goes to the default gateway's MAC.
- TLS does not fit OSI cleanly; say "sits above transport, below HTTP".

Try it (macOS/Linux):
```
$ ifconfig            # macOS (Linux: ip addr)       -> your IP, netmask, MAC
$ arp -a                                            -> IP-to-MAC cache on your LAN
$ netstat -rn         # macOS (Linux: ip route)     -> default gateway
default   192.168.1.1   UGScg   en0
```

Gotcha: "Layer 7 load balancer" can terminate TLS and route by header; an L4 one just forwards TCP and cannot see paths or cookies.

How interviewers probe it: "Which layer is a router/switch/LB?", "Where does TLS live?", "What changes at each hop and what does not?" Expect a follow-up like "why can't a L4 LB do path-based routing?"

---
## 2. IP addressing, subnets, CIDR

IPv4 = 32 bits, written as four octets. CIDR notation `a.b.c.d/N` means the first N bits are the network prefix; the remaining 32-N bits are host bits.

```
 192.168.10.0/24
 11000000.10101000.00001010 . 00000000
 |<------- 24 network ------>|<- 8 host ->|
 netmask 255.255.255.0
```

Formulas
- Addresses in block = 2^(32-N)
- Usable hosts (classic LAN) = 2^(32-N) - 2 (network address and broadcast excluded). Cloud providers reserve more (AWS reserves 5 per subnet; check current docs).
- Block size in the interesting octet = 256 - mask octet value.

Worked example 1: 10.0.0.0/16
- Host bits 16 -> 65,536 addresses. Range 10.0.0.0 - 10.0.255.255.

Worked example 2: split 192.168.1.0/24 into 4 subnets
- Need 4 subnets -> borrow 2 bits -> /26. Each has 2^6 = 64 addresses (62 usable).
```
 192.168.1.0/26    -> .0   - .63    (gw .1, broadcast .63)
 192.168.1.64/26   -> .64  - .127
 192.168.1.128/26  -> .128 - .191
 192.168.1.192/26  -> .192 - .255
```

Worked example 3: which subnet is 172.16.37.200/20 in?
- /20 -> mask 255.255.240.0; interesting octet is the 3rd; block size 256-240 = 16.
- 37 / 16 = 2 (floor) -> 2*16 = 32. Network = 172.16.32.0, broadcast = 172.16.47.255.
- Range 172.16.32.0 - 172.16.47.255 (4096 addresses).

Worked example 4: do 10.1.4.9 and 10.1.7.250 share a /22?
- /22 -> third-octet block size 4. 4 -> block 4-7; 7 -> block 4-7. Same network 10.1.4.0/22. Yes.

Worked example 5: smallest prefix for 500 hosts?
- 2^9 = 512 >= 502 needed (500 + 2) -> 9 host bits -> /23.

Common masks
```
 /8  255.0.0.0         /24 255.255.255.0     /28 255.255.255.240 (16 addrs)
 /16 255.255.0.0       /26 255.255.255.192   /30 255.255.255.252 (4 addrs, point-to-point)
 /32 single host       /0  everything (default route)
```

Special ranges
| Range | Meaning |
|---|---|
| 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 | RFC 1918 private (not routable on internet) |
| 127.0.0.0/8 | loopback (localhost) |
| 169.254.0.0/16 | link-local (DHCP failed; cloud metadata at 169.254.169.254) |
| 100.64.0.0/10 | carrier-grade NAT, also used by some VPNs (Tailscale) |
| 0.0.0.0 | "all interfaces" when binding; "this host" otherwise |

Routing: longest-prefix match wins. Routes 10.0.0.0/8 via A and 10.1.0.0/16 via B -> a packet to 10.1.2.3 goes via B.

NAT: many private hosts share one public IP; the NAT device rewrites src IP:port and keeps a table. Consequence: inbound connections cannot reach private hosts unless forwarded; NAT tables time out idle connections (a classic cause of "connection hangs after 5 minutes idle" -> use TCP keepalive).

IPv6: 128 bits, hex groups (2001:db8::1), /64 per subnet is standard, no NAT needed, no broadcast. Dual-stack clients prefer IPv6 ("Happy Eyeballs" falls back fast). Gotcha: a service listening only on IPv4 while DNS returns AAAA records can cause slow or failed connects.

Python check:
```python
import ipaddress
n = ipaddress.ip_network("172.16.37.200/20", strict=False)
print(n, n.num_addresses, n.network_address, n.broadcast_address)
# 172.16.32.0/20 4096 172.16.32.0 172.16.47.255
print(ipaddress.ip_address("10.1.7.250") in ipaddress.ip_network("10.1.4.0/22"))  # True
```

Gotcha: overlapping CIDRs between a customer's network and your VPC make VPC peering/VPN impossible. FDEs hit this constantly; ask for the customer's ranges early.

How interviewers probe it: "How many hosts in a /27?" (32, 30 usable), "Split a /24 into 8 subnets", "Why can't two peered networks overlap?", "What is longest-prefix match?"

---
## 3. TCP vs UDP

```
            TCP                              UDP
 connect    yes (handshake)                  no
 delivery   reliable, ordered, dedup         best effort, may drop/reorder
 model      byte stream (no msg boundaries)  datagrams (boundaries kept)
 control    flow + congestion control        none (app's job)
 overhead   20+ byte header, state           8 byte header, stateless
 use        HTTP/1-2, SSH, DB, SMTP          DNS, video/voice, games, QUIC (HTTP/3), DHCP
```

### 3.1 Three-way handshake

```
 Client                         Server (LISTEN)
   | --- SYN, seq=x ----------->  |   client -> SYN_SENT
   | <-- SYN+ACK, seq=y, ack=x+1  |   server -> SYN_RECEIVED
   | --- ACK, ack=y+1 --------->  |   both ESTABLISHED
   |  (data can flow; 1 RTT spent before first byte)
```
- Purpose: agree on initial sequence numbers and confirm both directions work.
- SYN flood: attacker sends SYNs and never ACKs, filling the server's half-open queue. Mitigation: SYN cookies.
- Two queues on the server: SYN queue (half-open) and accept queue (completed, waiting for `accept()`). `listen(backlog)` sizes the latter. A slow app that does not call accept fast enough drops connections (symptom: client timeouts under load).

### 3.2 Teardown (four-way) and TIME_WAIT

```
 Active closer                 Passive closer
   | --- FIN ------------------> |   FIN_WAIT_1
   | <-- ACK ------------------- |   FIN_WAIT_2 / passive: CLOSE_WAIT
   | <-- FIN ------------------- |   passive: LAST_ACK (after app calls close())
   | --- ACK ------------------> |   active: TIME_WAIT (2*MSL, ~60s on Linux; check current docs)
```
- TIME_WAIT lives on whoever closes first. It ensures late duplicate packets die out and that the final ACK can be retransmitted.
- Many TIME_WAIT sockets on a client/proxy -> ephemeral port exhaustion (~28k ports by default on Linux, range 32768-60999; check current docs). Fixes: connection pooling/keep-alive, widen port range, more source IPs. Do not "just disable it".
- Many CLOSE_WAIT sockets = your app forgot to close() after the peer closed. That is an application bug (leaked connections), not a kernel tuning issue.
- RST = abrupt abort. "Connection reset by peer" means the other side (or a middlebox) sent RST: crashed process, closed port, firewall, LB idle timeout.

### 3.3 Reliability: seq/ack, retransmits

- Every byte has a sequence number; receiver ACKs cumulatively ("I have everything up to N").
- Sender retransmits on: RTO timeout (exponential backoff, doubles each time) or 3 duplicate ACKs (fast retransmit, no waiting).
- Selective ACK (SACK) lets the receiver say which later ranges arrived, so only the holes are resent.
- Nagle's algorithm batches small writes; with delayed ACK it can add ~40ms latency to chatty request/response. Set TCP_NODELAY for latency-sensitive protocols.

### 3.4 Flow control vs congestion control

```
 Flow control       protects the RECEIVER. Receiver advertises a window (rwnd) in each ACK.
 Congestion control protects the NETWORK.  Sender keeps a congestion window (cwnd).
 Bytes in flight <= min(rwnd, cwnd)
```
- Zero window: receiver buffer full, sender pauses (probes periodically). Seen when an app reads slowly.
- Window scaling option allows windows beyond 64KB (needed for high bandwidth-delay-product links).
- Bandwidth-delay product (BDP) = bandwidth x RTT = bytes needed in flight to fill the pipe. 1 Gbps x 100ms = 12.5 MB. A small window caps throughput at window/RTT regardless of link speed.

Congestion control phases (classic Reno/CUBIC idea):
```
 cwnd
  ^            ssthresh
  |               .-----' congestion avoidance (+1 MSS per RTT, linear)
  |            .-'
  |          .'   <- slow start (cwnd doubles each RTT, exponential)
  |        .'
  |     .'          loss detected -> ssthresh = cwnd/2, then recover
  +-----------------------------------> time
```
- Slow start: begin with initial window (typically 10 segments, ~14KB; check current docs), double per RTT until ssthresh or loss.
- Congestion avoidance: grow linearly. On loss: multiplicative decrease (halve on triple-dup-ACK; reset harder on timeout).
- CUBIC is the Linux default; BBR (Google) models bandwidth and RTT rather than reacting to loss (check current docs for defaults).
- Why it matters: short HTTP responses never leave slow start; this is why fewer round trips (keep-alive, HTTP/2, TLS 1.3, CDN near the user) beat raw bandwidth.

Inspect on Linux/macOS:
```
$ ss -tan state established | head      # Linux; macOS: netstat -an -p tcp | grep ESTABLISHED
$ ss -ti dst 1.2.3.4                    # Linux: shows cwnd, rtt, retrans per socket
$ netstat -an | awk '/tcp/ {print $NF}' | sort | uniq -c   # count by state
   3 LISTEN
  42 ESTABLISHED
 120 TIME_WAIT
```

### 3.5 UDP in practice
- No handshake; sender can blast datagrams. Apps (QUIC, RTP) add their own reliability/pacing where needed.
- Datagrams larger than path MTU get fragmented (or dropped if DF set) -> keep UDP payloads < ~1200 bytes to be safe (QUIC does this).
- DNS uses UDP/53 for small answers and falls back to TCP/53 when truncated (TC bit) or for large responses/zone transfers. Firewalls that block TCP/53 cause rare, maddening failures.

Gotcha: "TCP is reliable" means ordered delivery to the kernel buffer, not that your peer processed the message. Without app-level acks, a write() success proves nothing about the remote handling it.

How interviewers probe it: "Walk the handshake", "Why TIME_WAIT?", "Slow start vs flow control?", "Server has 50k CLOSE_WAIT, what is wrong?", "Why does a single TCP stream not saturate a long fat pipe?"

---
## 4. DNS

DNS maps names to records. It is a hierarchical, distributed, heavily cached database.

```
 Browser -> OS stub resolver -> Recursive resolver (ISP / 8.8.8.8 / 1.1.1.1 / corp)
                                   |  (cache miss)
                                   |--1--> Root servers (.)         "who handles .com?"  -> NS for com
                                   |--2--> TLD servers (.com)       "who handles example.com?" -> NS
                                   |--3--> Authoritative NS         "A for www.example.com?" -> 93.184.216.34
                                   '--> caches answer for TTL, returns to client
```

Roles
- Stub resolver: tiny client in your OS/libc; asks the recursive resolver (see /etc/resolv.conf or `scutil --dns` on macOS).
- Recursive resolver: does the legwork and caches.
- Authoritative server: holds the truth for a zone; does not recurse.
- Delegation: NS records point down the tree; glue records break circularity (ns1.example.com needs an IP to be found).

Record types
| Type | Purpose | Example |
|---|---|---|
| A / AAAA | name -> IPv4 / IPv6 | api.example.com A 203.0.113.10 |
| CNAME | alias to another name (not allowed at zone apex) | www -> lb-123.elb.amazonaws.com |
| NS | delegates zone to name servers | example.com NS ns1... |
| MX | mail servers with priority | 10 mail.example.com |
| TXT | free text: SPF, DKIM, domain verification | "v=spf1 ..." |
| SRV | host+port for a service | _sip._tcp... |
| PTR | reverse lookup IP -> name | 10.113.0.203.in-addr.arpa |
| SOA | zone metadata, serial, negative-cache TTL | |
| CAA | which CAs may issue certs for the domain | 0 issue "letsencrypt.org" |

TTL and caching
- Each record has a TTL (seconds). Resolvers, OS, browsers, and even language runtimes cache it.
- Lower TTL before a migration (e.g. 300s a day ahead), then change, then raise it again. Changes are never instant; some resolvers ignore low TTLs.
- Negative caching: NXDOMAIN is cached too (governed by SOA minimum). Creating a record right after a failed lookup can still "not exist" for minutes.
- JVM/Python long-lived processes may resolve once and reuse the IP forever; after a failover they keep hitting the dead IP. Re-resolve or recycle connections.

Common patterns: round-robin DNS (several A records, crude load balancing), GeoDNS/latency routing, weighted records for canary, ALIAS/ANAME at apex for cloud LBs (Route 53 alias).

Security notes: DNSSEC signs records (integrity, not privacy). DoH/DoT encrypt the stub-to-resolver hop. Split-horizon DNS returns different answers inside vs outside the corporate network, so "works on my laptop, fails in the customer VPC" is often DNS.

Try it:
```
$ dig example.com +short
93.184.216.34
$ dig example.com A +noall +answer
example.com.  3600  IN  A  93.184.216.34        <- 3600 = remaining TTL
$ dig +trace example.com          # walk root -> TLD -> authoritative yourself
$ dig @8.8.8.8 example.com MX     # ask a specific resolver
$ dig -x 8.8.8.8 +short           # reverse lookup -> dns.google.
$ nslookup example.com            # simpler, interactive-capable
$ dig example.com | rg status     # status: NOERROR | NXDOMAIN | SERVFAIL | REFUSED
```
- NXDOMAIN = name does not exist. SERVFAIL = resolver could not get an answer (broken delegation, DNSSEC failure, upstream timeout). REFUSED = server won't answer you (ACL).

Gotcha: `/etc/hosts` and `nsswitch` order can override DNS; `dig` bypasses the OS resolver, while `ping`/`curl` use it. If dig works and curl fails, suspect the OS resolver config, search domains, or /etc/hosts. Also `ndots` in Kubernetes resolv.conf causes many wasted lookups for short names.

How interviewers probe it: "Recursive vs authoritative?", "Why can't CNAME be at the apex?", "You changed a record; users still see the old IP - why?", "Where would you check if dig works but the app fails?"

---
## 5. HTTP/1.1, HTTP/2, HTTP/3

HTTP is a request/response protocol: method + path + headers + optional body -> status + headers + body.

```
 GET /users/42 HTTP/1.1
 Host: api.example.com
 Accept: application/json
 Authorization: Bearer <token>

 HTTP/1.1 200 OK
 Content-Type: application/json
 Cache-Control: max-age=60
 {"id":42,"name":"Ada"}
```

### 5.1 HTTP/1.1
- Text protocol, persistent connections (keep-alive default), `Host` header enables virtual hosting.
- One request at a time per connection. Pipelining exists but is effectively unused due to head-of-line (HOL) blocking: response 2 cannot overtake slow response 1.
- Browsers open ~6 connections per host to parallelize; developers used domain sharding and bundling as hacks.

### 5.2 HTTP/2
- Binary framing, one TCP connection, many concurrent streams (multiplexing) -> no HTTP-level HOL blocking.
- HPACK header compression (headers repeat a lot), server push (deprecated in practice; check current docs), stream prioritization.
- Usually negotiated via TLS ALPN ("h2"). Browsers only do h2 over TLS.
- Remaining problem: TCP-level HOL blocking. One lost packet stalls ALL streams because TCP delivers in order. On lossy mobile networks h2 can be worse than multiple h1 connections.

```
 HTTP/1.1:  conn1 |==req1==|==req2==|        (serial per connection, 6 conns)
 HTTP/2:    conn  |s1 s3 s1 s5 s3 s1 ...|    (interleaved frames, 1 conn)
                    ^ lost packet blocks everything behind it (TCP HOL)
 HTTP/3:    QUIC  |s1|s3|s1|s5|   (UDP; loss only stalls the affected stream)
```

### 5.3 HTTP/3 and QUIC
- HTTP/3 runs on QUIC, which runs on UDP. QUIC implements reliability, congestion control, and TLS 1.3 itself, in user space.
- Independent streams: loss on one stream does not block others (fixes TCP HOL).
- Faster setup: transport + crypto handshake combined (1 RTT; 0-RTT resumption possible but replayable, so only for idempotent requests).
- Connection migration: connection ID, not the 4-tuple, identifies the session; a phone switching Wi-Fi to LTE keeps the connection.
- Discovery: browser first connects via h2, server advertises `Alt-Svc: h3=":443"`, browser upgrades next time (HTTPS DNS records can also hint). Some corporate firewalls block UDP/443, so clients must fall back to h2. Gotcha for FDEs.

| | 1.1 | 2 | 3 |
|---|---|---|---|
| Transport | TCP | TCP | QUIC/UDP |
| Format | text | binary | binary |
| Multiplexing | no | yes | yes |
| HOL blocking | HTTP + TCP | TCP only | none across streams |
| Header compression | no | HPACK | QPACK |
| Encryption | optional | de facto TLS | always (TLS 1.3 built in) |

Try it:
```
$ curl -sI --http1.1 https://example.com | head -1     HTTP/1.1 200 OK
$ curl -sI --http2   https://example.com | head -1     HTTP/2 200
$ curl -sI --http3   https://cloudflare.com | head -1  (needs curl built with HTTP/3; check current docs)
$ curl -sI https://www.google.com | rg -i alt-svc      alt-svc: h3=":443"; ma=2592000
```

Gotcha: HTTP/2 between client and LB does not imply HTTP/2 to your FastAPI app; many LBs terminate h2 and speak h1.1 to the backend. Uvicorn speaks h1.1 only (use hypercorn for h2; check current docs).

How interviewers probe it: "What is HOL blocking and which versions fix which kind?", "Why is QUIC on UDP?", "Why did h2 not fix everything?", "Why would HTTP/3 fail inside a customer network?"

---
## 6. HTTPS, TLS, certificates

TLS gives: confidentiality (encryption), integrity (tamper detection), authentication (server proves identity via certificate).

### 6.1 Ideas from first principles
- Asymmetric crypto (public/private keys) is slow but solves key exchange and signatures. Symmetric crypto (AES-GCM, ChaCha20) is fast and carries the bulk data.
- Handshake: authenticate server, agree on a shared secret via (EC)DHE key exchange, derive symmetric keys. Ephemeral DH gives forward secrecy: stealing the server key later does not decrypt recorded traffic.

### 6.2 TLS 1.3 handshake (1-RTT)

```
 Client                                         Server
   | ClientHello: versions, ciphers,              |
   |   key_share (client DH public), SNI, ALPN -> |
   |                                              | picks cipher, computes shared secret
   | <- ServerHello + key_share                   |
   | <- {EncryptedExtensions, Certificate,        |   (everything after ServerHello is encrypted)
   |     CertificateVerify, Finished}             |
   | {Finished} ------------------------------->  |
   | ===== application data (HTTP) ============== |
   Total: TCP handshake (1 RTT) + TLS (1 RTT) before first request byte.
```
- TLS 1.2 needed 2 RTT for the TLS part. TLS 1.3 removed weak ciphers/RSA key exchange; always forward secret.
- 0-RTT resumption: send data with the first flight using a prior session ticket; faster but replayable (only safe for idempotent requests).
- Session resumption (tickets) skips the full handshake on reconnect.

### 6.3 Certificates and chain of trust

```
 Root CA (self-signed, in OS/browser trust store)
    '-- signs --> Intermediate CA
                     '-- signs --> Leaf cert for api.example.com
 Server must send: leaf + intermediates (NOT the root).
 Client checks: signature chain to a trusted root, validity dates,
                hostname matches SAN, revocation (OCSP/CRL; check current docs), key usage.
```
- Identity is in the Subject Alternative Name (SAN) list, not the legacy CN.
- Wildcard *.example.com covers one label only (a.example.com, not a.b.example.com).
- Lifetimes keep shrinking (public certs are heading toward ~47 days; check current docs). Automate with ACME/Let's Encrypt.
- Private/internal CAs: corporate TLS-inspection proxies re-sign traffic with their own CA; clients must trust it or you get verification errors. Python `requests` uses certifi (its own bundle), not the OS store, unless configured (REQUESTS_CA_BUNDLE / SSL_CERT_FILE).

### 6.4 SNI
Server Name Indication: the client states the hostname in ClientHello (in plaintext, unless ECH is used; check current docs) so one IP:443 can serve many certificates. Old clients without SNI get a default cert -> name mismatch. When you `curl https://1.2.3.4`, no proper SNI is sent; use `--resolve host:443:IP`.

### 6.5 mTLS
Both sides present certificates. The server also verifies the client's cert against a trusted CA. Used for service-to-service auth (service mesh like Istio/Linkerd, SPIFFE identities), zero-trust, B2B APIs. Failure signature: handshake alert "bad certificate"/"certificate required".

### 6.6 Try it
```
$ openssl s_client -connect example.com:443 -servername example.com </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
subject=CN=example.com
issuer=C=US, O=..., CN=...
notBefore=...  notAfter=...
X509v3 Subject Alternative Name: DNS:example.com, DNS:www.example.com

$ openssl s_client -connect example.com:443 -servername example.com -showcerts   # full chain
    Verify return code: 0 (ok)          <- anything else: read it (20 = unable to get local issuer cert)
$ openssl s_client -connect example.com:443 -tls1_3 </dev/null | rg 'Protocol|Cipher'
$ curl -v https://example.com 2>&1 | rg -i 'ALPN|TLS|subject|issuer|expire'
$ curl --cacert corp-ca.pem https://internal.example.com     # trust a private CA
```

Gotcha: "unable to get local issuer certificate" usually means the server did not send the intermediate (fix server config), or the client lacks the corporate root CA. Never fix it with `verify=False` / `curl -k` in production code; it disables authentication entirely.

How interviewers probe it: "Walk the TLS handshake", "What does the CA actually sign?", "What is SNI and why needed?", "TLS 1.3 vs 1.2?", "How would you debug a cert error at a customer site?", "What is mTLS for?"

---
## 7. REST, status codes, headers, caching, CORS

### 7.1 REST essentials
Resources are nouns in URLs; HTTP methods are verbs; stateless requests; representations (JSON).

| Method | Semantics | Safe | Idempotent |
|---|---|---|---|
| GET | read | yes | yes |
| HEAD | headers only | yes | yes |
| POST | create / action | no | no (use Idempotency-Key) |
| PUT | replace | no | yes |
| PATCH | partial update | no | not guaranteed |
| DELETE | remove | no | yes |
| OPTIONS | capabilities / CORS preflight | yes | yes |

Idempotent = repeating has the same effect as once. Critical for safe client retries.

### 7.2 Status codes
```
 1xx info      101 Switching Protocols (WebSocket upgrade)
 2xx success   200 OK | 201 Created (+Location) | 202 Accepted (async) | 204 No Content
 3xx redirect  301 permanent | 302 found | 304 Not Modified | 307/308 keep method
 4xx client    400 bad syntax | 401 unauthenticated | 403 forbidden (authenticated, not allowed)
               404 not found | 405 method not allowed | 409 conflict | 415 unsupported media
               422 validation failed (FastAPI default) | 429 too many requests (+Retry-After)
 5xx server    500 internal | 502 bad gateway (upstream sent garbage/closed)
               503 unavailable (+Retry-After) | 504 gateway timeout (upstream too slow)
```
Gotcha: 401 vs 403 is a favorite. 401 = "I don't know who you are" (missing/invalid credentials); 403 = "I know who you are; no." 502 vs 504: 502 means the proxy got a bad or no response (upstream crashed/reset); 504 means the upstream did not answer within the proxy timeout.

### 7.3 Important headers
| Header | Role |
|---|---|
| Host | which site (required in 1.1) |
| Content-Type / Accept | body format / desired format |
| Authorization | credentials (Bearer, Basic) |
| Cache-Control, ETag, Last-Modified, Vary | caching |
| Location | redirect / created resource |
| X-Forwarded-For / Forwarded, X-Forwarded-Proto | original client info behind proxies |
| Retry-After | back-off hint for 429/503 |
| Strict-Transport-Security | force HTTPS for a period |
| User-Agent, Origin, Referer | client context |

### 7.4 Caching
```
 Request 1:  GET /logo.png        -> 200, Cache-Control: max-age=3600, ETag: "abc"
 (within 3600s)  served from cache, no network
 After expiry:  GET /logo.png, If-None-Match: "abc"
                -> 304 Not Modified (no body)   ... or 200 with new body + new ETag
```
- `Cache-Control: max-age=N` fresh for N seconds. `s-maxage` for shared caches (CDN). `public` / `private` (browser only; user-specific data). `no-cache` = may store but MUST revalidate. `no-store` = never store (secrets). `immutable` for fingerprinted assets. `stale-while-revalidate` serve stale while refreshing.
- ETag = opaque version validator; Last-Modified = timestamp validator. Conditional requests: If-None-Match / If-Modified-Since -> 304.
- `Vary: Accept-Encoding` (or Authorization, Accept-Language) tells caches which request headers change the response; wrong Vary leaks one user's response to another.
- Also use ETag + If-Match for optimistic concurrency on PUT (412 Precondition Failed on mismatch).

FastAPI example:
```python
from fastapi import FastAPI, Request, Response
import hashlib, json

app = FastAPI()

@app.get("/users/{uid}")
def get_user(uid: int, request: Request, response: Response):
    body = {"id": uid, "name": "Ada"}
    etag = '"' + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16] + '"'
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag})
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "private, max-age=30"
    return body
```

### 7.5 CORS
Same-origin policy: a page from origin A (scheme+host+port) cannot read responses from origin B. CORS lets B opt in via headers. It is enforced by the BROWSER; curl and servers ignore it. It protects users' browsers, not your API.

```
 Simple request (GET/POST with simple headers/content types):
   Browser sends Origin: https://app.example.com
   Server replies Access-Control-Allow-Origin: https://app.example.com  -> JS may read it

 Preflight (non-simple: PUT/DELETE, JSON content-type, Authorization header, custom headers):
   Browser -> OPTIONS /items
              Origin: https://app.example.com
              Access-Control-Request-Method: PUT
              Access-Control-Request-Headers: authorization,content-type
   Server  -> 204
              Access-Control-Allow-Origin: https://app.example.com
              Access-Control-Allow-Methods: PUT
              Access-Control-Allow-Headers: authorization,content-type
              Access-Control-Max-Age: 600        (cache the preflight)
   Browser then sends the real PUT.
```
- Credentials (cookies) require `Access-Control-Allow-Credentials: true` AND a specific origin; `*` is not allowed with credentials.
- A CORS error does not mean the server rejected the call; the request often reached the server (side effects happen for simple requests). Preflight failing (e.g. 401/404 on OPTIONS) is a common cause.

FastAPI:
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],   # not "*" with credentials
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["authorization", "content-type"],
    max_age=600,
)
```

Try it:
```
$ curl -i -X OPTIONS http://localhost:8000/items \
    -H 'Origin: https://app.example.com' \
    -H 'Access-Control-Request-Method: PUT'
HTTP/1.1 200 OK
access-control-allow-origin: https://app.example.com
access-control-allow-methods: GET, POST, PUT, DELETE
```

How interviewers probe it: "401 vs 403?", "PUT vs PATCH vs POST idempotency", "no-cache vs no-store", "How does ETag save bandwidth?", "Why does my curl work but the browser says CORS?", "What triggers a preflight?"

---
## 8. Cookies, sessions, tokens

HTTP is stateless; authentication state must ride on every request.

```
 Session (server-side state)               Token (stateless, e.g. JWT)
 login -> server stores session{id:user}   login -> server signs a token with claims
 sends  Set-Cookie: sid=abc123              client sends Authorization: Bearer <jwt>
 each request: cookie -> lookup in Redis    server verifies signature, no lookup
 + easy revoke, small cookie                + scales horizontally, cross-service
 - shared store needed                      - hard to revoke before expiry
```

Cookies
```
 Set-Cookie: sid=abc123; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=3600
```
| Attribute | Effect |
|---|---|
| HttpOnly | JS cannot read it (limits XSS token theft) |
| Secure | only sent over HTTPS |
| SameSite=Strict | never sent on cross-site requests |
| SameSite=Lax | sent on top-level GET navigations, not cross-site POST/subresources (browser default today; check current docs) |
| SameSite=None | sent cross-site; requires Secure |
| Domain/Path | scope; Domain=example.com includes subdomains |
| Max-Age/Expires | lifetime (otherwise session cookie) |
| __Host- prefix | forces Secure, Path=/, no Domain (strong scoping) |

Attacks and defenses
- CSRF: a malicious site makes the browser send your cookie to your bank. Defenses: SameSite, CSRF tokens, checking Origin. Pure Bearer-header APIs are not CSRF-prone (browser doesn't auto-attach).
- XSS: injected script steals tokens in localStorage; HttpOnly cookies are not readable by it (but XSS can still make requests as the user).
- Session fixation: regenerate session ID at login.

JWT (JSON Web Token): `base64url(header).base64url(payload).signature`
```
 header  {"alg":"RS256","typ":"JWT"}
 payload {"sub":"42","iss":"https://auth.example.com","aud":"my-api","exp":1767225600,"scope":"read"}
 signature = sign(header.payload, key)      <- payload is ENCODED, not encrypted
```
- Verify: signature, `exp`, `nbf`, `iss`, `aud`; pin allowed algorithms (reject `alg: none` and HS/RS confusion).
- HS256 = shared secret; RS256/ES256 = private key signs, public key (JWKS endpoint) verifies, so many services can verify without being able to mint.
- Short-lived access token (minutes) + refresh token (stored carefully, rotated) is the common pattern. Revocation needs a denylist or short expiry.
- OAuth2/OIDC: OAuth2 = delegated authorization (access tokens); OIDC adds identity (ID token). Authorization Code + PKCE is the standard browser/mobile flow.

FastAPI sketch:
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt  # PyJWT

bearer = HTTPBearer()

def current_user(cred: HTTPAuthorizationCredentials = Depends(bearer)):
    try:
        return jwt.decode(cred.credentials, PUBLIC_KEY, algorithms=["RS256"], audience="my-api")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="invalid token",
                            headers={"WWW-Authenticate": "Bearer"})
```
Setting a cookie in FastAPI: `response.set_cookie("sid", sid, httponly=True, secure=True, samesite="lax", max_age=3600)`.

Gotcha: storing JWTs in localStorage is XSS-exposed; storing in cookies requires CSRF thought. There is no free lunch; know the trade-off and say it.

How interviewers probe it: "Session vs JWT trade-offs?", "How do you log out a JWT user?", "What does SameSite do?", "Is a JWT encrypted?", "Design auth for a SPA + API."

---
## 9. Real-time: polling, long polling, SSE, WebSockets

```
 Short polling   client asks every N sec          wasteful, simple, high latency
 Long polling    client asks; server holds until   emulates push over plain HTTP; one
                 data or timeout, then client      request per event batch; works anywhere
                 immediately re-asks
 SSE             one long HTTP response,           server -> client only, text/event-stream,
                 server streams "data: ...\n\n"    auto-reconnect + Last-Event-ID, works over h2
 WebSocket       HTTP Upgrade -> full-duplex       bidirectional, binary/text frames, low
                 persistent TCP channel            overhead, you manage reconnect/heartbeats
```

| Need | Pick |
|---|---|
| Notifications, live feeds, LLM token streaming (server -> client) | SSE |
| Chat, collaborative editing, games (both directions, low latency) | WebSocket |
| Legacy/proxy-hostile environments, infrequent events | Long polling |
| Data changes rarely | Short polling with ETag |

WebSocket handshake:
```
 GET /ws HTTP/1.1
 Upgrade: websocket
 Connection: Upgrade
 Sec-WebSocket-Key: dGhlIHNhbXBsZQ==
 -> HTTP/1.1 101 Switching Protocols  + Sec-WebSocket-Accept: ...
```
Operational notes: LBs and proxies need long idle timeouts and upgrade support; use ping/pong heartbeats; stateful connections complicate scaling (sticky sessions or a pub/sub backplane like Redis); HTTP caching/CORS semantics differ; browsers don't send custom headers on WebSocket (auth via cookie, query token, or first message).

FastAPI:
```python
from fastapi import FastAPI, WebSocket
from fastapi.responses import StreamingResponse
import asyncio

app = FastAPI()

@app.websocket("/ws")
async def ws(sock: WebSocket):
    await sock.accept()
    while True:
        msg = await sock.receive_text()
        await sock.send_text(f"echo: {msg}")

@app.get("/events")
async def events():
    async def gen():
        for i in range(5):
            yield f"data: tick {i}\n\n"
            await asyncio.sleep(1)
    return StreamingResponse(gen(), media_type="text/event-stream")
```
Try SSE: `curl -N http://localhost:8000/events` prints a line per second (-N disables curl buffering). Reverse proxies that buffer (nginx default) break SSE; disable buffering (`X-Accel-Buffering: no`).

How interviewers probe it: "SSE vs WebSocket?", "How do you scale WebSockets to many servers?", "What breaks long-lived connections in corporate networks?"

---
## 10. What happens when you type a URL

```
 1. Browser parses URL: scheme=https host=www.example.com port=443 path=/
 2. HSTS list / cache check; may serve from HTTP cache directly
 3. DNS: browser cache -> OS cache -> /etc/hosts -> recursive resolver -> root/TLD/authoritative
         result: A/AAAA (and maybe HTTPS record)
 4. Routing: dest IP not on my subnet -> ARP for default gateway MAC -> frames to router
         (NAT at home router; many hops across ISPs/BGP)
 5. TCP handshake (SYN, SYN-ACK, ACK)           [HTTP/3: QUIC handshake over UDP instead]
 6. TLS handshake: ClientHello+SNI+ALPN, cert chain validated, keys derived
 7. HTTP request: GET / with Host, cookies, Accept-Encoding
 8. Edge: CDN/anycast -> L4/L7 load balancer -> (WAF, rate limit) -> app server (uvicorn/FastAPI)
         app may hit cache (Redis), DB, other services; builds response
 9. Response: status, headers, body (gzip/br); possibly 301/302 redirect -> repeat from step 3
10. Browser parses HTML -> discovers CSS/JS/images -> more requests (reuse the h2/h3 connection)
11. Render: DOM + CSSOM -> layout -> paint; JS executes; connection kept alive or closed
```
Cost model (cold, HTTP/1.1 + TLS 1.3): DNS (1 RTT+) + TCP (1 RTT) + TLS (1 RTT) + request (1 RTT) = about 4 RTTs before the first byte. This is why CDNs (shorter RTT), keep-alive, TLS resumption, HTTP/3, and DNS prefetch matter.

Good answers go deep on one area when asked. For a backend role, expand steps 8 (LB health checks, connection pools, timeouts); for infra, steps 3-6.

How interviewers probe it: they stop you at any step and ask "go deeper": "What if the DNS answer has multiple IPs?", "Who terminates TLS?", "What if the server is behind NAT?", "Where could caching occur?"

---
## 11. Command-line toolkit

```
 Symptom area        Tool                  What it tells you
 Name resolution     dig, nslookup, host   records, TTL, which resolver, status
 Reachability        ping, traceroute/mtr  ICMP reachability, per-hop latency/loss
 Port open?          nc -vz host port      TCP connect succeeded (open) or refused/timeout
 HTTP detail         curl -v/-w            DNS/TCP/TLS/TTFB timings, headers, redirects
 TLS/cert            openssl s_client      chain, SAN, dates, protocol, cipher
 Local sockets       ss / netstat / lsof   listening ports, states, owning process
 Packets             tcpdump / Wireshark   ground truth on the wire
```

curl
```
$ curl -v https://api.example.com/health          # request/response + TLS info (> sent, < received)
$ curl -sS -o /dev/null -w 'dns=%{time_namelookup} tcp=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total} code=%{http_code}\n' https://example.com
dns=0.012 tcp=0.034 tls=0.071 ttfb=0.110 total=0.112 code=200     <- values are cumulative
$ curl -L -I http://example.com                    # follow redirects, HEAD only
$ curl --resolve api.example.com:443:203.0.113.10 https://api.example.com/   # bypass DNS, keep SNI
$ curl --connect-timeout 3 --max-time 10 URL       # always set timeouts
$ curl -x http://proxy:3128 https://example.com    # via proxy (or env https_proxy)
$ curl -H 'Authorization: Bearer $TOKEN' -d '{"a":1}' -H 'content-type: application/json' URL
```

dig / nslookup: see section 4. Add `+short`, `+trace`, `@server`, `+tcp`.

ss / netstat / lsof
```
$ ss -ltnp                        # Linux: listening TCP + process (needs sudo for others' PIDs)
State  Local Address:Port  Process
LISTEN 0.0.0.0:8000        users:(("uvicorn",pid=4242,fd=7))
$ netstat -an -p tcp | rg LISTEN  # macOS (no -p process flag; -p is protocol on macOS)
$ lsof -iTCP -sTCP:LISTEN -P -n   # macOS/Linux: who owns which listening port
$ lsof -i :8000                   # who is using port 8000
$ lsof -p 4242 | wc -l            # file descriptors (sockets) held by a process
```
Reading `Local Address`: 127.0.0.1:8000 = reachable only from the same host; 0.0.0.0:8000 = all interfaces. "Works on localhost, not from outside" = bound to 127.0.0.1 (uvicorn default host is 127.0.0.1; use --host 0.0.0.0, and in Docker you must).

traceroute / mtr
```
$ traceroute -n example.com       # sends probes with increasing TTL; each router replies "time exceeded"
 1  192.168.1.1   1.2 ms
 2  10.20.0.1     8.9 ms
 3  * * *                         <- hop ignores/blocks probes (not necessarily a problem)
$ mtr -rwc 20 example.com         # continuous per-hop loss/latency (brew install mtr)
```
Gotcha: loss at an intermediate hop that does not continue to later hops is just ICMP rate limiting. Loss that persists to the destination is real.

tcpdump
```
$ sudo tcpdump -i any -nn 'host 203.0.113.10 and port 443' -c 20
$ sudo tcpdump -i en0 -nn 'tcp[tcpflags] & (tcp-syn|tcp-rst) != 0'     # only SYN/RST (macOS iface en0)
$ sudo tcpdump -i any -nn port 53                                      # watch DNS
$ sudo tcpdump -i any -nn -w cap.pcap port 8000                        # save for Wireshark
12:00:00.1 IP 10.0.0.5.51234 > 203.0.113.10.443: Flags [S], seq 1, win 64240, length 0     <- SYN
12:00:00.2 IP 203.0.113.10.443 > 10.0.0.5.51234: Flags [S.], ...                          <- SYN-ACK
12:00:00.2 IP 10.0.0.5.51234 > 203.0.113.10.443: Flags [.], ...                           <- ACK
```
Flags: S=SYN, .=ACK, F=FIN, R=RST, P=PSH. You cannot read HTTPS payload without keys (SSLKEYLOGFILE lets Wireshark decrypt browser/curl traffic).

openssl s_client: see section 6.6. Useful flags: `-servername`, `-showcerts`, `-tls1_2`, `-cert/-key` for mTLS, `-verify_return_error`, `-proxy host:port`.

How interviewers probe it: "Walk me through diagnosing slow requests with curl -w", "How do you know which process holds port 8000?", "What does a `*` in traceroute mean?"

---
## 12. Debugging playbook for customer environments

Method: reproduce from the failing vantage point, bisect by layer from the bottom up (DNS -> L3 reachability -> TCP -> TLS -> HTTP -> app), change one thing at a time, capture evidence. As an FDE you often cannot install tools or see their firewall; ask for specific command output and give copy-pasteable commands.

```
 Layer ladder (stop at the first failing rung):
  1 DNS resolves?           dig host / nslookup host
  2 IP reachable/routed?    ping, traceroute (ICMP may be blocked: absence of ping proves nothing)
  3 TCP port connects?      nc -vz host 443  /  curl -v telnet-style
  4 TLS completes?          openssl s_client -connect host:443 -servername host
  5 HTTP returns?           curl -v https://host/path
  6 App-level correct?      app logs, request IDs, auth, payload
```

### 12.1 DNS failures
- Symptoms: "Name or service not known", "Temporary failure in name resolution", `NXDOMAIN`, `SERVFAIL`; intermittent after a deploy.
- Check: `dig host` vs `dig @8.8.8.8 host` (resolver-specific?), `dig +trace host`, `cat /etc/resolv.conf`, `/etc/hosts`, search domains/ndots, split-horizon (internal vs public).
- Causes: private zone not reachable from that VPC/VPN, resolver blocks external DNS, stale cache/TTL, missing AAAA/A, TCP/53 blocked.

### 12.2 Connection refused vs timeout (high-frequency question)
```
 Connection refused (ECONNREFUSED)           Timeout (ETIMEDOUT / hang)
 Packet reached the host; the host sent RST  Packet got no answer at all
 because nothing listens on that port.       Silently dropped by a firewall/security group, wrong IP/route,
                                             host down, or reply path broken.
 Fast failure (ms).                          Slow failure (SYN retries: ~tens of seconds to minutes)
 Check: service running? bound to right      Check: security groups / NACLs / firewall, routing tables,
 interface/port? (ss -ltnp)                  NAT, VPN, is it the right IP?  (tcpdump: SYN out, no SYN-ACK back)
```
- Also: "connection reset" (RST mid-stream: proxy idle timeout, app crash, TLS-inspecting firewall, wrong protocol e.g. HTTP to a TLS port).
- Read vs connect timeouts differ: connect = network path; read = server accepted but did not respond in time (app slow, upstream stuck, DB lock). Always set both in clients (httpx.Timeout(connect=3, read=10)).
- tcpdump interpretation: SYN repeats with no reply -> drop upstream of you; RST immediately after SYN -> port closed or firewall reject.

### 12.3 Certificate errors
| Error | Likely cause | Fix |
|---|---|---|
| certificate has expired | cert not renewed (or client clock wrong) | renew; check `date` on client |
| hostname mismatch / SAN | wrong cert served (no SNI, wrong vhost) or hitting by IP | correct name, SNI, add SAN |
| unable to get local issuer | missing intermediate, or private/corporate CA not trusted | serve full chain; install CA / set SSL_CERT_FILE |
| self-signed in chain | TLS-inspection proxy or dev cert | trust the proxy CA properly |
| handshake failure / protocol version | TLS version or cipher mismatch (old client vs TLS 1.3-only, or reverse) | align min versions |
| bad certificate (mTLS) | client cert missing/untrusted | provide cert/key, correct CA |
Commands: `openssl s_client -connect host:443 -servername host -showcerts`, then `openssl x509 -noout -dates -subject -ext subjectAltName`. Compare what you see with what the customer's browser sees; a difference reveals an inspecting proxy (issuer is the corp CA).

### 12.4 Proxy / firewall issues
- Symptoms: works from laptop, fails from server; only certain ports/destinations fail; 407 Proxy Authentication Required; CONNECT tunnel failures; UDP/443 (HTTP/3) blocked; WebSockets die after idle.
- Check env vars (HTTP_PROXY, HTTPS_PROXY, NO_PROXY, case-sensitive variants) used by curl/requests/pip; PAC files; egress allowlists (need FQDN/IP lists, and note CDN IPs change).
- Ask the customer for: egress rules, proxy host/port, TLS inspection policy, idle timeouts on LB/firewall (often 60-350s), allowed protocols.
- Fixes: allowlist, NO_PROXY for internal hosts, enable keep-alives/heartbeats shorter than middlebox idle timeout, fall back from h3 to h2.

### 12.5 MTU / fragmentation
- MTU = max packet size on a link (Ethernet 1500; tunnels/VPN/overlay networks lose 20-100 bytes of it). MSS = TCP payload max (MTU - 40 for IPv4).
- Path MTU Discovery relies on ICMP "fragmentation needed" messages; firewalls that drop ICMP create a "PMTU black hole".
- Classic symptom: TCP connects, small requests (GET) work, large responses or TLS handshakes with big certificates hang; SSH logs in but freezes on `ls` of big output; works over home internet, fails over VPN.
- Test (DF bit): 
```
$ ping -D -s 1472 host      # macOS: -D sets Don't Fragment; Linux: ping -M do -s 1472 host
(1472 + 28 header bytes = 1500). If 1472 fails but 1372 works, path MTU is lower.
```
- Fixes: lower MTU on tunnel interface, MSS clamping on the gateway/VPN, allow ICMP type 3 code 4.

### 12.6 "Slow" and intermittent issues
- Use `curl -w` timing breakdown to localize: high dns -> resolver; high connect -> network/route; high tls -> handshake/cert chain/OCSP; high ttfb -> server/app; high total-minus-ttfb -> payload/bandwidth.
- Intermittent: multiple A records with one bad backend (`dig +short` shows several; test each with --resolve), IPv6 vs IPv4 path difference (`curl -4` vs `-6`), LB idle-timeout resets, connection pool reusing stale connections (retry on idempotent requests), ephemeral port exhaustion (`ss -s`, many TIME_WAIT), DNS caching after failover.
- Sockets and FDs: `ulimit -n`, `lsof -p PID | wc -l`; "Too many open files" looks like a network error.
- Always capture: exact timestamps and timezone, source/destination IP:port, request ID, client and server logs, the output of the ladder commands. Timestamps let you line up server logs, LB logs, and packet captures.

Customer-facing habits
- State what you checked and what it ruled out; ask for one specific artifact at a time.
- Prefer read-only diagnostics first; avoid asking for `-k` workarounds as a "fix".
- Write the final root cause with the layer, the evidence, the fix, and a prevention (monitoring, cert-expiry alert, runbook).

How interviewers probe it: scenario questions - "Customer says the API times out only from their data center. Walk me through it." Good answers follow the ladder, ask clarifying questions (since when? all clients? which protocol/ports?), and name what each result implies.

---
## 13. FastAPI networking checklist

```python
# run:  uvicorn app:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

@app.get("/whoami")
def whoami(request: Request):
    # behind a proxy the TCP peer is the proxy; real client is in X-Forwarded-For
    return {"peer": request.client.host,
            "xff": request.headers.get("x-forwarded-for"),
            "proto": request.url.scheme}

client = httpx.AsyncClient(timeout=httpx.Timeout(connect=3, read=10, write=10, pool=5),
                           limits=httpx.Limits(max_connections=100, max_keepalive_connections=20))
```
- Bind 0.0.0.0 in containers; expose port; health endpoint for LB checks (/healthz).
- Trust X-Forwarded-* only from known proxies (spoofable otherwise).
- Reuse one HTTP client (connection pooling) to avoid handshake cost and TIME_WAIT piles.
- Set timeouts everywhere; add retries with exponential backoff + jitter only for idempotent calls; honor Retry-After.
- Graceful shutdown: stop accepting, drain in-flight, so LBs don't send RSTs mid-deploy; keep app keep-alive timeout greater than the LB idle timeout (to avoid races where the app closes a connection the LB thinks is alive; uvicorn `--timeout-keep-alive`, default 5s; check current docs).

Gotcha: 502s that appear sporadically after idle periods are often exactly this keep-alive race.

How interviewers probe it: "Why do I see 127.0.0.1 as the client IP?", "Why intermittent 502s from the ALB?", "How would you configure timeouts for a service calling a flaky dependency?"

---
## 14. Self-check (answer aloud)

1. Which layer does a router, a switch, an ALB, an NLB operate at?
2. Is 10.4.130.77 inside 10.4.128.0/21? (block 8 in 3rd octet: 128-135 -> yes)
3. Server shows 40k CLOSE_WAIT vs 40k TIME_WAIT; what does each imply?
4. Why does a small initial congestion window hurt small responses on high-RTT links?
5. dig works, curl says "could not resolve host". Next steps?
6. What does h2 fix and what does it leave unfixed? What does QUIC do about it?
7. Draw the TLS 1.3 handshake and say what is encrypted when.
8. Why does the browser send an OPTIONS before PUT, and who answers it?
9. JWT vs server session for revocation, scaling, and XSS/CSRF exposure.
10. A customer reports the app hangs after 5 minutes idle through their firewall; hypotheses and fixes?
